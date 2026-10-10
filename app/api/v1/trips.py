"""Trip management: create (pickup -> drop-off), start, complete, route."""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from ...models.driver import Driver
from ...models.trip import TRIP_STATUSES, Trip
from ...models.vehicle import Vehicle
from ...schemas.trip import TripCreate, TripOut
from ..deps import authed_db

router = APIRouter(prefix="/trips", tags=["trips"])

WAYPOINT_COUNT = 10


def build_waypoints(pickup_lat: float, pickup_lng: float,
                    dropoff_lat: float, dropoff_lng: float,
                    count: int = WAYPOINT_COUNT) -> str:
    """Straight-line interpolation between pickup and drop-off.

    Pure geometry for the demo map — no routing service, no ML.
    """
    points = []
    for i in range(count + 1):
        frac = i / count
        points.append([
            round(pickup_lat + (dropoff_lat - pickup_lat) * frac, 6),
            round(pickup_lng + (dropoff_lng - pickup_lng) * frac, 6),
        ])
    return json.dumps(points)


@router.post("", response_model=TripOut, status_code=201)
def create_trip(payload: TripCreate, db=Depends(authed_db)):
    if not db.get(Driver, payload.driver_id):
        raise HTTPException(status_code=400, detail="Driver not found")
    if not db.get(Vehicle, payload.vehicle_id):
        raise HTTPException(status_code=400, detail="Vehicle not found")
    trip = Trip(
        **payload.model_dump(),
        waypoints=build_waypoints(
            payload.pickup_lat, payload.pickup_lng,
            payload.dropoff_lat, payload.dropoff_lng,
        ),
        status="PLANNED",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


@router.get("", response_model=list[TripOut])
def list_trips(status: str | None = None, db=Depends(authed_db)):
    query = db.query(Trip).order_by(Trip.id.desc())
    if status:
        if status not in TRIP_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid status")
        query = query.filter(Trip.status == status)
    return query.all()


@router.get("/{trip_id}", response_model=TripOut)
def get_trip(trip_id: int, db=Depends(authed_db)):
    trip = db.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("/{trip_id}/start", response_model=TripOut)
def start_trip(trip_id: int, db=Depends(authed_db)):
    trip = db.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.status != "PLANNED":
        raise HTTPException(status_code=400, detail="Only PLANNED trips can start")
    trip.status = "ACTIVE"
    trip.started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(trip)
    return trip


@router.post("/{trip_id}/complete", response_model=TripOut)
def complete_trip(trip_id: int, db=Depends(authed_db)):
    trip = db.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Only ACTIVE trips can complete")
    trip.status = "COMPLETED"
    trip.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(trip)
    return trip
