from pydantic import BaseModel


class LocationData(BaseModel):
    latitude: str | float | None = None
    longitude: str | float | None = None
    zip: str | int | None = None
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
    
class LogModel(BaseModel):
    message: str
    severity: str
    timestamp: str