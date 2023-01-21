from pydantic import BaseModel


class LocationData(BaseModel):
    latitude: str | None = None
    longitude: str | None = None
    zip: str | None = None
    countryCode: str = "IN"
    state: str | None = None
    city: str | None = None
    addressLine1: str | None = None
    addressLine2: str | None = None

class BaseUser(BaseModel):
    email: str

class ReturnUser(BaseUser):
    location_data: LocationData

class DbUser(BaseUser):
    lat: str
    lng: str
    passw: str
    timestamp: str