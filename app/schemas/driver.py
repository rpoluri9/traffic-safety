"""Driver schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DriverCreate(BaseModel):
    full_name: str
    license_number: str
    phone: str = ""


class DriverUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None


class DriverOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    license_number: str
    phone: str
    created_at: datetime
    safety_score: int | None = None
