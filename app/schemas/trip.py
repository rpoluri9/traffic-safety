"""Trip schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TripCreate(BaseModel):
    driver_id: int
    vehicle_id: int
    pickup_name: str
    pickup_lat: float
    pickup_lng: float
    dropoff_name: str
    dropoff_lat: float
    dropoff_lng: float


class TripOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    driver_id: int
    vehicle_id: int
    pickup_name: str
    pickup_lat: float
    pickup_lng: float
    dropoff_name: str
    dropoff_lat: float
    dropoff_lng: float
    waypoints: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
