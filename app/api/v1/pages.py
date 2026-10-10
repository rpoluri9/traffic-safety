"""Server-rendered dashboard pages (public demo UI)."""
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.rules import safety_score
from ...db.session import get_db
from ...models.driver import Driver
from ...models.trip import Trip
from ...models.violation import SEVERITIES, VIOLATION_TYPES, Violation

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, **extra):
    base = {"request": request, "api_key": settings.api_key,
            "violation_types": VIOLATION_TYPES, "severities": SEVERITIES}
    base.update(extra)
    return base


@router.get("/", response_class=HTMLResponse)
def page_dashboard(request: Request, db: Session = Depends(get_db)):
    recent = db.query(Violation).order_by(Violation.id.desc()).limit(10).all()
    drivers = db.query(Driver).order_by(Driver.id).all()
    for d in drivers:
        d.score = safety_score([v.severity for v in d.violations])
    return templates.TemplateResponse(
        "dashboard.html",
        _ctx(request, recent=recent, drivers=drivers),
    )


@router.get("/drivers", response_class=HTMLResponse)
def page_drivers(request: Request, db: Session = Depends(get_db)):
    drivers = db.query(Driver).order_by(Driver.id).all()
    for d in drivers:
        d.score = safety_score([v.severity for v in d.violations])
        d.violation_count = len(d.violations)
    return templates.TemplateResponse("drivers.html", _ctx(request, drivers=drivers))


@router.get("/trips", response_class=HTMLResponse)
def page_trips(request: Request, db: Session = Depends(get_db)):
    trips = db.query(Trip).order_by(Trip.id.desc()).all()
    drivers = db.query(Driver).order_by(Driver.id).all()
    return templates.TemplateResponse(
        "trips.html", _ctx(request, trips=trips, drivers=drivers)
    )


@router.get("/trips/{trip_id}", response_class=HTMLResponse)
def page_trip_detail(trip_id: int, request: Request, db: Session = Depends(get_db)):
    trip = db.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    route = json.loads(trip.waypoints or "[]")
    return templates.TemplateResponse(
        "trip_detail.html", _ctx(request, trip=trip, route_json=json.dumps(route))
    )


@router.get("/violations", response_class=HTMLResponse)
def page_violations(
    request: Request,
    type: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Violation).order_by(Violation.id.desc())
    if type in VIOLATION_TYPES:
        query = query.filter(Violation.type == type)
    if severity in SEVERITIES:
        query = query.filter(Violation.severity == severity)
    return templates.TemplateResponse(
        "violations.html",
        _ctx(request, violations=query.limit(100).all(),
             active_type=type or "", active_severity=severity or ""),
    )
