"""Driver model."""
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    license_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(30), default="")
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="driver")
    trips: Mapped[list["Trip"]] = relationship(back_populates="driver")
    violations: Mapped[list["Violation"]] = relationship(back_populates="driver")
