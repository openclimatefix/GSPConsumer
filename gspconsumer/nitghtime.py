""" Add zeros to nightime """

import logging
import os
from datetime import datetime

import pandas as pd
import pvlib
from nowcasting_datamodel.models.gsp import LocationSQL

logger = logging.getLogger(__name__)

# the elevation limit for night time, decided to go for 5 degrees, as almost all
# solar panels will have zero production when the sun is at this elevation
elevation_limit = os.getenv("ELEVATION_LIMIT", 5)

# get lat and longs of the gsps
dir = os.path.dirname(__file__)
gsp_locations_file = os.path.join(dir, "data/uk_gsp_locations.csv")
gsp_locations = pd.read_csv(gsp_locations_file)
gsp_locations = gsp_locations.set_index("gsp_id")


def make_night_time_zeros(
    start: datetime,
    end: datetime,
    gsp: LocationSQL,
    gsp_yield_df: pd.DataFrame,
    regime: str,
):
    """
    Set generation to zero if it is night time

    :param start: The start datetimes we are looking for
    :param end: The end datetimes we are looking for
    :param gsp:
    :param gsp_yield_df:
    :param regime:
    :return:
    """

    if regime != "in-day":
        return gsp_yield_df

    gsp_location = gsp_locations.loc[gsp.gsp_id]
    longitude = gsp_location["longitude"]
    latitude = gsp_location["latitude"]

    times = pd.date_range(start=start, end=end, freq="30min")
    # check if it is nighttime, and if so, set generation values to zero
    solpos = pvlib.solarposition.get_solarposition(
        time=times, longitude=longitude, latitude=latitude, method="nrel_numpy"
    )
    elevation = solpos["elevation"]

    # only keep nighttime values
    elevation = elevation[elevation < elevation_limit]

    # last capacity is
    if gsp.last_gsp_yield is not None:
        last_capacity = gsp.last_gsp_yield.capacity_mwp
        last_pvlive_updated_utc = gsp.last_gsp_yield.pvlive_updated_utc
    else:
        last_capacity = 0
        last_pvlive_updated_utc = start

    gsp_yield_df = pd.DataFrame(
        {
            "generation_mw": 0,
            "datetime_gmt": elevation.index,
            "installedcapacity_mwp": last_capacity,
            "capacity_mwp": last_capacity,
            "updated_gmt": last_pvlive_updated_utc,
        }
    )

    return gsp_yield_df
