import re
import time
import json
import config
import requests
import pandas as pd
from src import user
from src import helpers
from itertools import zip_longest
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By


db = config.DB
logger = config.LOGGER


class Keka:
    def __init__(self, user: user.User):
        self.user = user

    def save_state(self, punch_type: config.PunchType):
        data = {
            "email": self.user.email,
            "punch_status": punch_type.value,
            "timestamp": datetime.now(self.user.timezone).isoformat(),
        }
        db.upsert_record(config.STATE_DB, data, self.user.email)
        logger.info("Saved state")


    def retrieve_state(self):
        data: dict = db.read_record(config.STATE_DB, self.user.email)
        punch_message = config.punch_message_map[data.get("punch_status", 2)]
        punch_status = config.PunchType(data.get("punch_status", 2))
        timestamp = datetime.strptime(
            data.get("timestamp", datetime.now(self.user.timezone).isoformat()),
            config.DATETIME_FORMAT,
        )
        message = helpers.format_time_delta(
            f"{punch_message} ", datetime.now(self.user.timezone) - timestamp, " ago"
        )
        logger.info(message)
        return punch_status, timestamp


    def make_request(self, url: str, method: str = "GET", data: dict = None, params: dict = None):
        if url.startswith("/") and config.KEKA_BASE_API_URL.endswith("/"):
            url = url[1:]

        config.HEADERS["authorization"] = f"Bearer {self.get_token()}"
        response = requests.request(
            method,
            config.KEKA_BASE_API_URL + url,
            headers=config.HEADERS,
            data=json.dumps(data),
            params=params,
        )
        return response


    def get_or_ingest_data(self, url: str, method: str = "GET",
        ingest=False, db_path: str = None, data: dict = None, params: dict = None
    ):
        response = self.make_request(url, method=method, data=data, params=params)
        if response.status_code != 200:
            logger.error(f"Error getting {url}! Response code: {response.status_code}")
            return {}
        response = response.json()
        if ingest:
            db.upsert_record(db_path, response | {"email": self.user.email}, self.user.email)
        return response


    def get_leaves_for_date(self, dt: datetime):
        return self.get_or_ingest_data(
            "/me/leave/calendarevents",
            params={"fromDate": dt.isoformat(), "toDate": dt.isoformat()}
        )


    def get_work_time_for_date(self, dt: datetime):
        data = self.get_or_ingest_data(
            "/mytime/attendance/attendancerequests",
            params={"fromDate": dt.isoformat(), "toDate": dt.isoformat()},
        )
        clockin_requests = [
            y
            for x in data.get("remoteClockInRequests", [])
            for y in x.get("timeEntries", [])
            if x.get("requestDate") == dt.isoformat()
        ]
        if len(clockin_requests) == 0:
            return timedelta(seconds=0)
        df = pd.DataFrame.from_records(clockin_requests)[["punchStatus", "actualTimestamp"]]
        if len(df)%2 == 1 or df.iloc[-1]["punchStatus"] != 1:
            last_punch_ts = datetime.fromisoformat(df.iloc[-1]["actualTimestamp"])
            df.loc[len(df)] = (
                [1, last_punch_ts.isoformat()] if last_punch_ts.date() == dt
                else [1, datetime.now().isoformat()]
            )

        return timedelta(seconds=sum(map(
            lambda x: (datetime.fromisoformat(x[1]) - datetime.fromisoformat(x[0])).total_seconds(),
            df.groupby("punchStatus")
            .agg({"actualTimestamp": list})
            .transpose()
            .apply(lambda x: zip_longest(x[0], x[1], fillvalue=datetime.now()), axis=1)
            .iloc[0]
        )))
    

    def get_keka_profile(self):
        return self.get_or_ingest_data("/me/publicprofile")


    def is_leave(self, dt: datetime):
        keka_user_id = self.get_keka_profile().get("id")
        leaves = self.get_leaves_for_date(dt)
        print(leaves)
        leaves = list(filter(
            lambda x: (x.get("employeeId") == keka_user_id)
            and ("2023-01-09" in [x.get("fromDate"), x.get("toDate")]),
            leaves.get("teamLeaveRequests", [])
        ))
        return len(leaves) > 0


    def is_holiday_or_weekend(self, dt: datetime):
        is_first_day_of_year = dt.timetuple().tm_yday == 1
        holidays = db.read_record(config.HOLIDAYS_DB, self.user.email)
        if not holidays or is_first_day_of_year:
            holidays = self.get_or_ingest_data("/dashboard/holidays", ingest=True, db_path=config.HOLIDAYS_DB)
        is_holiday = dt in [datetime.fromisoformat(holiday.get("date")).date() for holiday in holidays.get("value")]
        is_weekend = dt.weekday() in [5, 6]
        return is_holiday or is_weekend


    def punch(self, punch_type: config.PunchType | None = None, force: bool = False):
        if punch_type == config.PunchType.NO_PUNCH:
            return 200, config.SUCCESS

        if not self.user.location_data.city:
            raise ValueError("Location data is not set")

        last_punch_status, last_punch_time = self.retrieve_state()

        # If punch_type is not provided, then we will punch the opposite of the last punch
        if punch_type is None:
            punch_type = config.PunchType(1 - (
                last_punch_status.value if last_punch_status.value in [0, 1] else 1
            ))

        user_current_time = datetime.now(self.user.timezone)
        
        if not force:
            if last_punch_status == punch_type:
                return 400, helpers.format_time_delta(
                    f"Already {config.punch_message_map[punch_type.value]} ",
                    user_current_time - last_punch_time, " ago"
                )
            if self.is_holiday_or_weekend(user_current_time.date()):
                return 400, "It's a holiday or weekend. Not punching"
            if self.is_leave(user_current_time.date()):
                return 400, "Relax! You are on leave today..."

        json_data = {
            "attendanceLogSource": 1,
            "locationAddress": self.user.location_data.dict(),
            "manualClockinType": 3,
            "note": "",
            "originalPunchStatus": punch_type.value,
            "timestamp": user_current_time.replace(tzinfo=None).isoformat()[:-3] + "Z",
        }

        response = self.make_request("/mytime/attendance/remoteclockin", "POST", json_data)
        if response.status_code == 200:
            self.save_state(punch_type)
            logger.info(config.punch_message_map[punch_type.value])
        else:
            logger.error(
                f"Error!!! Status Code: {response.status_code}, Response: {response.text}"
            )

        return (
            (200, config.punch_message_map[punch_type.value])
            if response.status_code == 200
            else (response.status_code, response.text)
        )


    def get_token_age(self, timestamp: datetime = None, now: datetime = None, auto_load = False):
        if auto_load:
            data: dict = db.read_record(config.TOKEN_DB, self.user.email) or {}
            saved_email = data.get("email", "")
            timestamp = (
                datetime(2020, 1, 1, tzinfo=self.user.timezone)
                if data.get("timestamp") is None or saved_email != self.user.email
                else datetime.strptime(data.get("timestamp"), config.DATETIME_FORMAT)
            )

        now = now if now else datetime.now(self.user.timezone)
        token_age = now - timestamp
        logger.log(
            20 if auto_load else 10,
            helpers.format_time_delta("Token is ", token_age, " old"),
        )
        return token_age, timestamp if auto_load else None


    def get_token(
        self, max_age: timedelta = timedelta(days=6, hours=12), max_retries: int = 3
    ):
        data: dict = db.read_record(config.TOKEN_DB, self.user.email)

        saved_email = data.get("email", "")
        timestamp = data.get("timestamp")

        # added the email check to avoid using the token of another user
        timestamp = (
            datetime(2020, 1, 1, 0, 0, 0, tzinfo=self.user.timezone).strftime(config.DATETIME_FORMAT)
            if timestamp is None or saved_email != self.user.email
            else timestamp
        )
        token_age, _ = self.get_token_age(
            datetime.strptime(timestamp, config.DATETIME_FORMAT)
        )

        while token_age > max_age and max_retries > 0:
            if token_age > max_age:
                logger.info(f"Token was last refreshed at {timestamp}. Refreshing token...")
                data = self.refresh_token()
            token_age, _ = self.get_token_age(
                datetime.strptime(
                    data.get("timestamp", timestamp), config.DATETIME_FORMAT
                )
            )
            max_retries -= 1
            logger.info(f"Retrying to get token. Retries left: {max_retries}")

        token = data.get("token")
        return token


    def login(self, email: str, password: str, headless=False):
        driver = helpers.get_chrome_driver(headless=headless, enable_logs=True)
        driver.get(config.KEKA_LOGIN_URL)
        time.sleep(15)

        driver.find_element(
            By.XPATH, '//*[@id="login-container-center"]/div/div/div[3]/form/button[2]'
        ).click()
        time.sleep(5)

        driver.find_element(By.ID, "email").send_keys(email)
        time.sleep(1)

        driver.find_element(By.ID, "password").send_keys(password)
        time.sleep(1)

        driver.find_element(
            By.XPATH,
            '//*[@id="login-container-center"]/div/div/form/div/div[4]/div/button',
        ).click()
        # TODO: Add a check to see if login was successful
        logger.info("Login successful")
        time.sleep(5)

        return driver


    def refresh_token(self, headless=True):
        if not (self.user.email and self.user.passw):
            logger.exception("Email or password is not set")

        driver = self.login(self.user.email, self.user.passw, headless=headless)
        request_logs: list[dict] = driver.get_log("performance")
        data = {"email": self.user.email}

        for x in request_logs:
            token = re.findall(r"(?:Bearer\s)([a-zA-Z0-9]+)", str(x))
            if token:
                request_log = json.loads(x.get("message", "{}"))
                request_log["email"] = self.user.email
                db.upsert_record("requests", request_log, self.user.email)
                data["token"] = token[0]
                data["timestamp"] = datetime.now(self.user.timezone).isoformat()
                break

        if "token" in data:
            db.upsert_record(config.TOKEN_DB, data, self.user.email)
            logger.info(f"Token has been updated!")
        else:
            logger.info("Token not found!")

        return data


