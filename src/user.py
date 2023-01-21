import config
from src import helpers
from src.models import *
from datetime import datetime
from pytz import timezone, country_timezones
from src.log_utils import cloud_logger as logger


db = config.DB

class User:
    def __init__(self, email: str = None, passw: str = None, lat=None, lng=None):
        self.email = email if email else config.KEKA_USERNAME
        self.passw = passw if passw else config.KEKA_PASSWORD
        self.lat = lat if lat else config.USER_LAT
        self.lng = lng if lng else config.USER_LNG

        self.location_data = self.get_location(self.lat, self.lng)

        self.timezone = timezone(
            country_timezones(self.location_data.countryCode)[0]
        )

        self.current_time = datetime.now(self.timezone)
        self.save_user()


    def save_user(self):
        data = DbUser(
            email=self.email,
            passw=helpers.encode_password(self.passw),
            lat=self.lat,
            lng=self.lng,
            timestamp=self.current_time.isoformat(),
        )
        db.upsert_record(config.USERS_DB, data.dict(), self.email)
        logger().info(f"Saved user {self.email}")


    def get_user(self):
        return ReturnUser(email=self.email, location_data=self.location_data)


    def get_location(self, lat: str, lng: str):
        location_data = db.read_record(config.LOCATION_DB, f"{lat},{lng}", [])
        if location_data:
            location_data = LocationData.parse_obj(location_data)
            logger().info(f"Using cached location: {location_data.addressLine1}")
            return location_data

        location = helpers.reverse_geocode(lat, lng)
        address = location.address if location else None
        if not location:
            logger().error("Unable to reverse geocode location")
        else:
            logger().info(f"Using Location: {address}")
        location_data = LocationData(
            latitude=lat,
            longitude=lng,
            zip=location.raw.get("address", {}).get("postcode"),
            countryCode=location.raw.get("address", {}).get("country_code", "in").upper(),
            state=location.raw.get("address", {}).get("state"),
            city=location.raw.get("address", {}).get("city"),
            addressLine1=address,
            addressLine2=location.raw.get("address", {}).get("city"),
        ) if location else LocationData()
        
        db.upsert_record(config.LOCATION_DB, location_data.dict(), f"{lat},{lng}")
        return location_data
