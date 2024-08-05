""" GSP functions """

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from nowcasting_datamodel.models.gsp import LocationSQL
from nowcasting_datamodel.read.read import get_all_locations, get_location
from nowcasting_datamodel.read.read_gsp import get_latest_gsp_yield
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_gsps(
    session: Session, n_gsps: int = 339, regime: str = "in-day", include_national: bool = True
) -> List[LocationSQL]:
    """
    Get PV systems

    1. Load from database
    3. add any gsp not in database

    :param session: database sessions
    :param n_gsps: number of gsps, 0 is national then 1 to 338 is the gsps
    :param regime: if its "in-day" or "day-after"
    :param include_national: optionl if to get national data or not
    :return: list of gsps sqlalchemy objects
    """
    gsp_ids = list(range(1, n_gsps + 1))
    if include_national:
        gsp_ids = [0] + gsp_ids
    total_n_gsps = len(gsp_ids)

    # load all pv systems in database
    locations_sql_db: List[LocationSQL] = get_all_locations(session=session, gsp_ids=gsp_ids)

    logger.debug(
        f"Found {len(locations_sql_db)} locations in the database, should be {total_n_gsps}"
    )

    # get missing gsps
    if len(locations_sql_db) < total_n_gsps:
        gsp_ids_in_db = [location.gsp_id for location in locations_sql_db]
        missing_gsp_ids = [gsp_id for gsp_id in gsp_ids if gsp_id not in gsp_ids_in_db]

        logger.debug(f"There were {len(missing_gsp_ids)} missing gsp in the database")

        new_locations = []
        for gsp_id in missing_gsp_ids:
            location = get_location(session=session, gsp_id=gsp_id)
            new_locations.append(location)

        all_locations = new_locations + locations_sql_db

    elif len(locations_sql_db) > total_n_gsps:
        logger.warning(
            f"There were {len(locations_sql_db)} GSPS in the database, "
            f"should only be {total_n_gsps}"
        )

        seen = set()
        dupes = [x.gsp_id for x in locations_sql_db if x.gsp_id in seen or seen.add(x)]
        gsp_ids_and_labels = [(x.gsp_id, x.label) for x in locations_sql_db]
        raise Exception(f"The duplicate gsp ids are {dupes}, for all {gsp_ids_and_labels}")

    else:
        all_locations = locations_sql_db

    assert (
        len(all_locations) == total_n_gsps
    ), f"Found {len(locations_sql_db)} locations in the database, should be {total_n_gsps}"

    # Only get data that is 1 week odd
    datetime_utc = datetime.now(timezone.utc) - timedelta(days=7)

    logger.debug("Get latest GSP yields")
    all_locations = get_latest_gsp_yield(
        session=session,
        append_to_gsps=True,
        gsps=all_locations,
        regime=regime,
        datetime_utc=datetime_utc,
    )

    assert len(all_locations) == total_n_gsps, len(all_locations)

    return all_locations


def filter_gsps_which_have_new_data(
    gsps: List[LocationSQL], datetime_utc: Optional[datetime] = None
):
    """
    Filter gsps which have new data available

    This is done by looking at the datestamp of last data pulled,
    add then by looking at the pv system refresh time, we can determine if new data is available

    sudo code:
        if last_datestamp + refresh_interval > datetime_now
            keep = True

    Args:
        gsps: list of gsps
        datetime_utc: the datetime now

    Returns: list of pv systems that have new data.

    """

    logger.info(f"Looking at which GSP might have new data. Number of GSPs are {len(gsps)}")

    if datetime_utc is None:
        datetime_utc = datetime.now(timezone.utc)

    keep_gsps = []
    for i, gsp in enumerate(gsps):
        logger.debug(f"Looking at {i}th GSP, out of {len(gsps)} gsps")

        last_yield = gsp.last_gsp_yield

        if last_yield is None:
            # there is no pv yield data for this pv system, so lets keep it
            logger.debug(
                f"There is no gsp yield data for GSP {gsp.gsp_id}, " f"so will be getting data "
            )
            keep_gsps.append(gsp)
        else:
            next_datetime_data_available = timedelta(minutes=30) + last_yield.datetime_utc
            if next_datetime_data_available < datetime_utc:
                logger.debug(
                    f"For gsp {gsp.gsp_id} as "
                    f"last yield datetime is {last_yield.datetime_utc},"
                    f"refresh interval is 30 minutes, "
                    f"so will be getting data"
                )
                keep_gsps.append(gsp)
            else:
                logger.debug(
                    f"Not keeping gsp {gsp.gsp_id} as "
                    f"last yield datetime is {last_yield.datetime_utc},"
                    f"refresh interval is 30 minutes"
                )

    return keep_gsps
