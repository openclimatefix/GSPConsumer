""" Time helper functions """

import logging
from datetime import datetime, timezone

import pytz

logger = logging.getLogger(__name__)


def check_uk_london_hour(hour: int):
    """
    Check that the UK London hour is the same as given value

    We want to pull the data at 10.30 (local time) for national GSP.
    Becasue we use CRON in UTC, we need to run the code at
    10.30 UTC (winter) and 9.30 UTC in (summer).
    In the winter we want the 9.30 trigger, not to pull any day.

    Therefore an error is rasied if UK London hour does not match the given hour.

    :param hour: The expected hour of UK london
    """

    logger.debug(f"Checking that UK London hour is same as {hour}")

    # only check if 'hour' is not None
    if hour is None:
        return None

    now_utc = datetime.now(tz=timezone.utc)
    now_uk_london = now_utc.astimezone(pytz.timezone("Europe/London"))

    if hour != now_uk_london.hour:
        raise Exception(
            f"Expected UK london hour to be {hour} but it was {now_uk_london}. "
            f"We will now not run the code."
        )
