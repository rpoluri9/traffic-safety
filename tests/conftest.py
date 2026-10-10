"""Pytest fixtures: isolated SQLite DB, API-key header helper."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.driver import Driver
from app.models.vehicle import Vehicle

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Test app skips table creation: the db fixture manages the SQLite schema.
app = create_app(init_db=False)

API_KEY = settings.api_key


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_driver(db, name="Test Driver", license_no="DL-9001") -> Driver:
    d = Driver(full_name=name, license_number=license_no, phone="+15550009999")
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def make_vehicle(db, driver_id=None, plate="TST-0001") -> Vehicle:
    v = Vehicle(plate_number=plate, make="Test", model="Car", year=2020, driver_id=driver_id)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def auth_headers():
    return {"X-API-Key": API_KEY}
