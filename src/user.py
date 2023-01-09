import config
from src import db
from src import helpers
from typing import AnyStr
from datetime import datetime
from pytz import timezone, country_timezones
from src.log_utils import cloud_logger as logger


class User:
    def __init__(self, email: AnyStr = None, passw: AnyStr = None, lat = None, lng = None):
        self.email = email if email else config.KEKA_USERNAME
        self.passw = passw if passw else config.KEKA_PASSWORD
        
        self.lat = lat if lat else config.USER_LAT
        self.lng = lng if lng else config.USER_LNG
        
        self.location_data = self.get_location(self.lat, self.lng)
        
        self.timezone = timezone(
            country_timezones(self.location_data.get("countryCode", "IN"))[0]
        )
        
        self.user_current_time = datetime.now(self.timezone)
        self.save_user()
    
    
    def save_user(self):
        data = {
            "email": self.email,
            "passw": helpers.encode_password(self.passw),
            "lat": self.lat,
            "lng": self.lng,
            "timestamp": self.user_current_time.isoformat(),
        }
        db.upsert_record(config.USERS_DB, data, self.email)
        logger().info(f"Saved user {self.email}")
    
    
    def get_location(self, lat, lng):
        location_data = db.read_record(config.LOCATION_DB, f"{lat},{lng}", [])
        if location_data:
            logger().info(f"Using cached location: {location_data.get('addressLine1')}")
            return location_data
        
        location = helpers.reverse_geocode(lat, lng)
        address = location.address if location else None
        if not location:
            logger().error("Unable to reverse geocode location")
        else:
            logger().info(f"Using Location: {address}")
        location_data = (
            {
                "latitude": lat,
                "longitude": lng,
                "zip": location.raw.get("address", {}).get("postcode"),
                "countryCode": location.raw.get("address", {}).get("country_code", "in").upper(),
                "state": location.raw.get("address", {}).get("state"),
                "city": location.raw.get("address", {}).get("city"),
                "addressLine1": address,
                "addressLine2": location.raw.get("address", {}).get("city"),
            }
            if location
            else None
        )
        db.upsert_record(config.LOCATION_DB, location_data, f"{lat},{lng}")
        return location_data
