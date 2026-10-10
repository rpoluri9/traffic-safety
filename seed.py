"""Seed demo data: drivers, vehicles, trips, and sample violations."""
import json

from app.core.rules import TelemetryInput, evaluate_telemetry
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.driver import Driver
from app.models.trip import Trip
from app.models.vehicle import Vehicle
from app.models.violation import Alert, Violation
from app.api.v1.trips import build_waypoints

ALERT_SEVERITIES = {"HIGH", "CRITICAL"}


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    drivers = [
        Driver(full_name="Arun Patel", license_number="DL-1001", phone="+15550001001"),
        Driver(full_name="Sara Khan", license_number="DL-1002", phone="+15550001002"),
        Driver(full_name="Mike Chen", license_number="DL-1003", phone="+15550001003"),
    ]
    db.add_all(drivers)
    db.flush()

    vehicles = [
        Vehicle(plate_number="ABC-1234", make="Toyota", model="Camry", year=2021, driver_id=drivers[0].id),
        Vehicle(plate_number="XYZ-5678", make="Honda", model="Civic", year=2019, driver_id=drivers[1].id),
        Vehicle(plate_number="LMN-9012", make="Ford", model="Transit", year=2022, driver_id=drivers[2].id),
    ]
    db.add_all(vehicles)
    db.flush()

    trips = [
        Trip(driver_id=drivers[0].id, vehicle_id=vehicles[0].id,
             pickup_name="Downtown Garage", pickup_lat=42.3601, pickup_lng=-71.0589,
             dropoff_name="Airport Terminal", dropoff_lat=42.3650, dropoff_lng=-71.0490,
             waypoints=build_waypoints(42.3601, -71.0589, 42.3650, -71.0490),
             status="COMPLETED"),
        Trip(driver_id=drivers[1].id, vehicle_id=vehicles[1].id,
             pickup_name="Central Station", pickup_lat=42.3520, pickup_lng=-71.0550,
             dropoff_name="Harbor View", dropoff_lat=42.3700, dropoff_lng=-71.0400,
             waypoints=build_waypoints(42.3520, -71.0550, 42.3700, -71.0400),
             status="PLANNED"),
    ]
    db.add_all(trips)
    db.flush()

    # Scripted telemetry producing one of each violation type.
    script = [
        dict(speed=72, speed_limit=50, heading=90, road_direction=90, signal_state="green",
             at_intersection=False, phone_in_use=False, alcohol_level=0.0, seatbelt_on=True,
             lat=42.361, lng=-71.057, trip_id=trips[0].id),                       # OVERSPEED
        dict(speed=45, speed_limit=50, heading=90, road_direction=90, signal_state="red",
             at_intersection=True, phone_in_use=False, alcohol_level=0.0, seatbelt_on=True,
             lat=42.362, lng=-71.056, trip_id=trips[0].id),                       # SIGNAL_CROSS
        dict(speed=50, speed_limit=50, heading=270, road_direction=90, signal_state="green",
             at_intersection=False, phone_in_use=False, alcohol_level=0.0, seatbelt_on=True,
             lat=42.363, lng=-71.055, trip_id=trips[0].id),                       # WRONG_WAY
        dict(speed=40, speed_limit=50, heading=90, road_direction=90, signal_state="green",
             at_intersection=False, phone_in_use=True, alcohol_level=0.0, seatbelt_on=True,
             lat=42.364, lng=-71.054, trip_id=trips[1].id),                       # MOBILE_USE
        dict(speed=30, speed_limit=50, heading=90, road_direction=90, signal_state="green",
             at_intersection=False, phone_in_use=False, alcohol_level=0.12, seatbelt_on=True,
             lat=42.365, lng=-71.053, trip_id=trips[1].id),                       # DRUNK_DRIVE
        dict(speed=55, speed_limit=50, heading=90, road_direction=90, signal_state="green",
             at_intersection=False, phone_in_use=False, alcohol_level=0.0, seatbelt_on=False,
             lat=42.366, lng=-71.052, trip_id=trips[1].id),                       # NO_SEATBELT (+OVERSPEED)
    ]
    driver_ids = [drivers[0].id, drivers[0].id, drivers[0].id,
                  drivers[1].id, drivers[1].id, drivers[2].id]
    vehicle_ids = [vehicles[0].id, vehicles[0].id, vehicles[0].id,
                   vehicles[1].id, vehicles[1].id, vehicles[2].id]

    for point, driver_id, vehicle_id in zip(script, driver_ids, vehicle_ids):
        hits = evaluate_telemetry(TelemetryInput(driver_id=driver_id, vehicle_id=vehicle_id, **point))
        for hit in hits:
            v = Violation(driver_id=driver_id, vehicle_id=vehicle_id, trip_id=point["trip_id"],
                          type=hit.violation_type, severity=hit.severity, message=hit.message,
                          speed=hit.speed, speed_limit=hit.speed_limit,
                          lat=hit.lat, lng=hit.lng)
            db.add(v)
            db.flush()
            if hit.severity in ALERT_SEVERITIES:
                db.add(Alert(violation_id=v.id, severity=hit.severity,
                             message=f"[{hit.severity}] {hit.message}"))
    db.commit()
    print(f"Seeded {len(drivers)} drivers, {len(vehicles)} vehicles, "
          f"{len(trips)} trips, {db.query(Violation).count()} violations, "
          f"{db.query(Alert).count()} alerts.")
    db.close()


if __name__ == "__main__":
    main()
