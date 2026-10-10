"""Violation / alert / telemetry schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TelemetryIn(BaseModel):
    driver_id: int
    vehicle_id: int
    trip_id: int | None = None
    speed: float = Field(default=0.0, ge=0)
    speed_limit: float = Field(default=50.0, gt=0)
    heading: float = Field(default=0.0, ge=0, le=359)
    road_direction: float = Field(default=0.0, ge=0, le=359)
    signal_state: str = Field(default="green", pattern="^(red|yellow|green)$")
    at_intersection: bool = False
    phone_in_use: bool = False
    alcohol_level: float = Field(default=0.0, ge=0)
    seatbelt_on: bool = True
    lat: float = 0.0
    lng: float = 0.0


class ViolationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    driver_id: int
    vehicle_id: int
    trip_id: int | None
    type: str
    severity: str
    message: str
    speed: float
    speed_limit: float | None
    lat: float
    lng: float
    created_at: datetime


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    violation_id: int
    severity: str
    message: str
    acknowledged: bool
    created_at: datetime


class TelemetryResult(BaseModel):
    violations: list[ViolationOut]
    alerts: list[AlertOut]
