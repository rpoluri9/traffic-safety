"""Trip model: pickup -> drop-off navigation with route waypoints."""
from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base

TRIP_STATUSES = ("PLANNED", "ACTIVE", "COMPLETED")


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"))
    pickup_name: Mapped[str] = mapped_column(String(160))
    pickup_lat: Mapped[float] = mapped_column(Float)
    pickup_lng: Mapped[float] = mapped_column(Float)
    dropoff_name: Mapped[str] = mapped_column(String(160))
    dropoff_lat: Mapped[float] = mapped_column(Float)
    dropoff_lng: Mapped[float] = mapped_column(Float)
    waypoints: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of [lat, lng]
    status: Mapped[str] = mapped_column(String(20), default="PLANNED", index=True)
    started_at: Mapped["DateTime | None"] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped["DateTime | None"] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    driver: Mapped["Driver"] = relationship(back_populates="trips")
    vehicle: Mapped["Vehicle"] = relationship(back_populates="trips")
    violations: Mapped[list["Violation"]] = relationship(back_populates="trip")
