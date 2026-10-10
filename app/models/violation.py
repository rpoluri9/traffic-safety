"""Violation and Alert models."""
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base

VIOLATION_TYPES = (
    "OVERSPEED",
    "SIGNAL_CROSS",
    "WRONG_WAY",
    "MOBILE_USE",
    "DRUNK_DRIVE",
    "NO_SEATBELT",
)
SEVERITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[int] = mapped_column(primary_key=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"))
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("trips.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(20), index=True)
    severity: Mapped[str] = mapped_column(String(10), index=True)
    message: Mapped[str] = mapped_column(Text, default="")
    speed: Mapped[float] = mapped_column(Float, default=0.0)
    speed_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    lat: Mapped[float] = mapped_column(Float, default=0.0)
    lng: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    driver: Mapped["Driver"] = relationship(back_populates="violations")
    vehicle: Mapped["Vehicle"] = relationship(back_populates="violations")
    trip: Mapped["Trip | None"] = relationship(back_populates="violations")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="violation")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    violation_id: Mapped[int] = mapped_column(ForeignKey("violations.id"))
    severity: Mapped[str] = mapped_column(String(10), index=True)
    message: Mapped[str] = mapped_column(Text, default="")
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    violation: Mapped["Violation"] = relationship(back_populates="alerts")
