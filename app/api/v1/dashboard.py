"""Dashboard stats + per-driver safety scores."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func

from ...core.rules import safety_score
from ...models.driver import Driver
from ...models.trip import Trip
from ...models.violation import SEVERITIES, VIOLATION_TYPES, Alert, Violation
from ..deps import authed_db

router = APIRouter(tags=["dashboard"])


def _driver_score(db, driver_id: int) -> int:
    severities = [
        row[0]
        for row in db.query(Violation.severity)
        .filter(Violation.driver_id == driver_id)
        .all()
    ]
    return safety_score(severities)


@router.get("/dashboard/stats")
def dashboard_stats(db=Depends(authed_db)):
    by_type = {
        row[0]: row[1]
        for row in db.query(Violation.type, func.count(Violation.id))
        .group_by(Violation.type)
        .all()
    }
    by_severity = {
        row[0]: row[1]
        for row in db.query(Violation.severity, func.count(Violation.id))
        .group_by(Violation.severity)
        .all()
    }
    # Violations per day for the last 7 days
    since = datetime.now(timezone.utc) - timedelta(days=7)
    per_day_rows = (
        db.query(func.date(Violation.created_at), func.count(Violation.id))
        .filter(Violation.created_at >= since)
        .group_by(func.date(Violation.created_at))
        .order_by(func.date(Violation.created_at))
        .all()
    )
    drivers = db.query(Driver).all()
    scores = [_driver_score(db, d.id) for d in drivers]
    return {
        "total_violations": db.query(func.count(Violation.id)).scalar() or 0,
        "critical_alerts": db.query(func.count(Alert.id))
        .filter(Alert.severity == "CRITICAL")
        .scalar()
        or 0,
        "unacknowledged_alerts": db.query(func.count(Alert.id))
        .filter(Alert.acknowledged.is_(False))
        .scalar()
        or 0,
        "active_trips": db.query(func.count(Trip.id))
        .filter(Trip.status == "ACTIVE")
        .scalar()
        or 0,
        "total_drivers": len(drivers),
        "avg_safety_score": round(sum(scores) / len(scores), 1) if scores else 100.0,
        "by_type": {t: by_type.get(t, 0) for t in VIOLATION_TYPES},
        "by_severity": {s: by_severity.get(s, 0) for s in SEVERITIES},
        "per_day": [{"day": str(day), "count": count} for day, count in per_day_rows],
    }


@router.get("/drivers/{driver_id}/safety-score")
def driver_safety_score(driver_id: int, db=Depends(authed_db)):
    driver = db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    violations = (
        db.query(Violation).filter(Violation.driver_id == driver_id).all()
    )
    return {
        "driver_id": driver_id,
        "safety_score": safety_score([v.severity for v in violations]),
        "violation_count": len(violations),
    }
