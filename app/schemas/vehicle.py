"""Vehicle schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VehicleCreate(BaseModel):
    plate_number: str
    make: str = ""
    model: str = ""
    year: int = 2020
    driver_id: int | None = None


class VehicleUpdate(BaseModel):
    make: str | None = None
    model: str | None = None
    year: int | None = None
    driver_id: int | None = None


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plate_number: str
    make: str
    model: str
    year: int
    driver_id: int | None
    created_at: datetime
