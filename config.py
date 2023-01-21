import os
from src.db import get_db
from enum import Enum, IntEnum
from dotenv import load_dotenv

DB = get_db()

# read from .env file
load_dotenv()

KEKA_USERNAME = os.environ.get("KEKA_USERNAME", "")
KEKA_PASSWORD = os.environ.get("KEKA_PASSWORD", "")

USER_LAT = os.environ.get("USER_LAT", 22.4809532)
USER_LNG = os.environ.get("USER_LNG", 88.4112943)

USER_TIMEZONE = os.environ.get("USER_TIMEZONE", "Asia/Kolkata")

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# CHROME_DRIVER_PATH = PROJECT_ROOT + "/chromedriver"

SUCCESS = "Success"
FAIL = "Fail"


class AllowedPunchType(IntEnum):
    PUNCH_IN = 0
    PUNCH_OUT = 1

class PunchType(IntEnum):
    PUNCH_IN = 0
    PUNCH_OUT = 1
    NO_PUNCH = 2


punch_message_map = {
    0: "Clocked In",
    1: "Clocked Out",
    2: "No Punch",
}


USERS_DB = "users"
STATE_DB = "state"
TOKEN_DB = "token"
LOCATION_DB = "location"
HOLIDAYS_DB = "holidays"
LEAVE_SUMMARY_DB = "leave_summary"
PENDING_APPROVALS_DB = "pending_approvals"


KEKA_SUBDOMAIN = os.environ.get("KEKA_SUBDOMAIN", "fiftyfive")

KEKA_LOGIN_URL = f"https://{KEKA_SUBDOMAIN}.keka.com/"
KEKA_BASE_API_URL = f"https://{KEKA_SUBDOMAIN}.keka.com/k/dashboard/api/"


USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
)
HEADERS = {
    "authority": f"{KEKA_SUBDOMAIN}.keka.com",
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "content-type": "application/json; charset=UTF-8",
    # "cookie": f"Subdomain={KEKA_SUBDOMAIN}.keka.com; ai_user=7/hhVf6MHcITcngvgwPwZ9|2022-09-26T04:46:51.086Z; ai_session=ki0vn6eex9JVH8dsEGLcTZ|1673029920475|1673029937351",
    "origin": f"https://{KEKA_SUBDOMAIN}.keka.com",
    "referer": f"https://{KEKA_SUBDOMAIN}.keka.com/",
    "sec-ch-ua": '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": USER_AGENT,
    "x-requested-with": "XMLHttpRequest",
}
