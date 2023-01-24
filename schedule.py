import time
import random
import config
import datetime
from src.keka import Keka
from src.user import User
from scheduler import Scheduler
from src.helpers import format_time_delta
from scheduler.trigger.core import Sunday


user = User()
keka = Keka(user)

logger = config.LOGGER
schedule = Scheduler(tzinfo=datetime.timezone.utc)


def refresh_token():
    keka.refresh_token(headless=True)


def punch(punch_type: config.PunchType):
    sleep_time = random.randint(2, 600)
    logger.info(f"Sleeping for another {sleep_time} seconds before {punch_type.value}")
    time.sleep(sleep_time)
    status_code, message = keka.punch(punch_type, force=False)
    logger.info(f"{message}, Status Code: {status_code}")


TOKEN_ROTATION_TIME = Sunday(datetime.time(hour=22, minute=44, tzinfo=user.timezone))
PUNCH_IN_TIME       = datetime.time(hour=10, minute=00, tzinfo=user.timezone)
PUNCH_OUT_TIME      = datetime.time(hour=20, minute=00, tzinfo=user.timezone)


schedule.weekly(TOKEN_ROTATION_TIME, refresh_token)
schedule.daily(PUNCH_IN_TIME, punch, args=(config.PunchType.PUNCH_IN,))
schedule.daily(PUNCH_OUT_TIME, punch, args=(config.PunchType.PUNCH_OUT,))


try:
    while True:
        logger.info(f"Ran {schedule.exec_jobs()} job(s) now")
        current_time = datetime.datetime.now(user.timezone)
        logger.info(
            "; ".join([
            format_time_delta(
                f"{x.handle.__name__}{tuple(str(y) for y in x.args)} will run after ", (x.datetime - current_time),
            ) 
            for x in schedule.get_jobs()])
        )
        time_to_run_jobs = [x.timedelta() for x in schedule.get_jobs()]
        least_delta = min(time_to_run_jobs)
        least_delta = least_delta if least_delta.total_seconds() > 0 else 1
        logger.info(format_time_delta("Sleeping for ", least_delta))
        time.sleep(least_delta.total_seconds())
except KeyboardInterrupt:
    print()