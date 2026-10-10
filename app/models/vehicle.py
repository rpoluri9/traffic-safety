"""Vehicle model."""
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    make: Mapped[str] = mapped_column(String(60), default="")
    model: Mapped[str] = mapped_column(String(60), default="")
    year: Mapped[int] = mapped_column(Integer, default=2020)
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"), nullable=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    driver: Mapped["Driver | None"] = relationship(back_populates="vehicles")
    trips: Mapped[list["Trip"]] = relationship(back_populates="vehicle")
    violations: Mapped[list["Violation"]] = relationship(back_populates="vehicle")
