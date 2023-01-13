import re
import time
import json
import config
import requests
from src import db
from src import user
from src import helpers
from typing import AnyStr, Dict, List
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from src.log_utils import cloud_logger as logger


class Keka:
    def __init__(self, user: user.User):
        self.user = user
    
    def save_state(self, punch_type: config.PunchType):
        data = {
            "email": self.user.email,
            "punch_status": punch_type.value,
            "timestamp": self.user.user_current_time.isoformat(),
        }
        db.upsert_record(config.STATE_DB, data, self.user.email)
        logger().info("Saved state") 
    
    
    def retrieve_state(self):
        data: Dict = db.read_record(config.STATE_DB, self.user.email)
        punch_message = config.punch_message_map[data.get("punch_status", 2)]
        punch_status = config.PunchType(data.get("punch_status", 2))
        timestamp = datetime.strptime(
            data.get("timestamp", datetime.now(self.user.timezone).isoformat()),
            config.DATETIME_FORMAT,
        )
        message = helpers.format_time_delta(
            f"{punch_message} ", datetime.now(self.user.timezone) - timestamp, " ago"
        )
        logger().info(message)
        return punch_status, timestamp
    
    
    def make_request(self, url: AnyStr, method: AnyStr = "GET", data: Dict = None):
        if url.startswith("/") and config.KEKA_BASE_API_URL.endswith("/"):
            url = url[1:]
        
        config.HEADERS["authorization"] = f"Bearer {self.get_token()}"
        response = requests.request(
            method,
            config.KEKA_BASE_API_URL + url,
            headers=config.HEADERS,
            data=json.dumps(data),
        )
        return response
    
    
    def is_holiday_or_weekend(self, dt: datetime):
        is_first_day_of_year = dt.timetuple().tm_yday == 1
        holidays = db.read_record(config.HOLIDAYS_DB, self.user.email)
        if not holidays or is_first_day_of_year:
            self.ingest_holidays()
            holidays = db.read_record(config.HOLIDAYS_DB, self.user.email)
        is_holiday = dt in [datetime.fromisoformat(holiday.get("date")).date() for holiday in holidays.get("value")]
        is_weekend = dt.weekday() in [5, 6]
        return is_holiday or is_weekend


    def punch(self, punch_type: config.PunchType | None = None, force: bool = False):
        if punch_type == config.PunchType.NO_PUNCH:
            return 200, config.SUCCESS
        
        if not self.user.location_data:
            raise ValueError("Location data is not set")

        last_punch_status, last_punch_time = self.retrieve_state()
        
        # If punch_type is not provided, then we will punch the opposite of the last punch
        if punch_type is None:
            punch_type = config.PunchType(1 - (
                last_punch_status.value if last_punch_status.value in [0, 1] else 1
            ))
        
        if last_punch_status == punch_type and not force:
            return 400, f"Already {config.punch_message_map[punch_type.value]}"
        
        user_current_time = self.user.user_current_time
        if self.is_holiday_or_weekend(user_current_time.date()) and not force:
            return 400, "It's a holiday or weekend. Not punching"
        
        json_data = {
            "attendanceLogSource": 1,
            "locationAddress": self.user.location_data,
            "manualClockinType": 3,
            "note": "",
            "originalPunchStatus": punch_type.value,
            "timestamp": user_current_time.replace(tzinfo=None).isoformat()[:-3] + "Z",
        }
        
        response = self.make_request("/mytime/attendance/remoteclockin", "POST", json_data)
        if response.status_code == 200:
            self.save_state(punch_type)
            logger().info(config.punch_message_map[punch_type.value])
        else:
            logger().error(
                f"Error!!! Status Code: {response.status_code}, Response: {response.text}"
            )
        
        return (
            (200, config.punch_message_map[punch_type.value])
            if response.status_code == 200
            else (response.status_code, response.text)
        )
    
    
    def ingest_holidays(self):
        response = self.make_request("/dashboard/holidays")
        if response.status_code != 200:
            logger().error("Error getting holidays! Response code:", response.status_code)
            return config.FAIL
        db.upsert_record(config.HOLIDAYS_DB, response.json(), self.user.email)
        return config.SUCCESS


    def ingest_pending_approvals(self):
        response = self.make_request("/inbox/pendingapprovalscount")
        if response.status_code != 200:
            logger().error("Error getting pending approvals! Response code:", response.status_code)
            return config.FAIL
        data = response.json()
        data["email"] = self.user.email
        db.upsert_record(config.PENDING_APPROVALS_DB, data, self.user.email)
        return config.SUCCESS


    def ingest_leave_summary(self, for_date: AnyStr = None):
        for_date = for_date or self.user.user_current_time.strftime("%Y-%m-%d")
        response = self.make_request(f"me/leave/summary?forDate={for_date}")
        if response.status_code != 200:
            logger().error("Error getting leave summary! Response code:", response.status_code)
            return config.FAIL
        data = response.json()
        data["email"] = self.user.email
        db.upsert_record(config.LEAVE_SUMMARY_DB, data, self.user.email)
        return config.SUCCESS


    def get_token_age(self, timestamp: datetime = None, now: datetime = None, auto_load = False):
        if auto_load:
            data: Dict = db.read_record(config.TOKEN_DB, self.user.email) or {}
            saved_email = data.get("email", "")
            timestamp = (
                datetime(2020, 1, 1, tzinfo=self.user.timezone)
                if data.get("timestamp") is None or saved_email != self.user.email
                else datetime.strptime(data.get("timestamp"), config.DATETIME_FORMAT)
            )
            
        now = now if now else datetime.now(self.user.timezone)
        print(now, timestamp)
        token_age = now - timestamp
        logger().log(
            20 if auto_load else 10,
            helpers.format_time_delta("Token is ", token_age, " old"),
        )
        return token_age, timestamp if auto_load else None


    def get_token(
        self, max_age: timedelta = timedelta(days=6, hours=12), max_retries: int = 3
    ):
        data: Dict = db.read_record(config.TOKEN_DB, self.user.email) or {}
        
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
                logger().info(f"Token was last refreshed at {timestamp}. Refreshing token...")
                data = self.refresh_token()
            token_age, _ = self.get_token_age(
                datetime.strptime(
                    data.get("timestamp", timestamp), config.DATETIME_FORMAT
                )
            )
            max_retries -= 1
            logger().info(f"Retrying to get token. Retries left: {max_retries}")

        token = data.get("token")
        return token


    def login(self, email: AnyStr, password: AnyStr, headless=False):
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
        logger().info("Login successful")
        time.sleep(5)

        return driver


    def refresh_token(self, headless=False):
        if not (self.user.email and self.user.passw): 
            logger().exception("Email or password is not set")
        
        driver = self.login(self.user.email, self.user.passw, headless=headless)
        request_logs: List[Dict] = driver.get_log("performance")
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
            logger().info(f"Token has been updated!")
        else:
            logger().info("Token not found!")

        return data
    

