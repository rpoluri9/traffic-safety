"""Telemetry ingestion: runs the rules engine, stores violations + alerts."""
from fastapi import APIRouter, Depends, HTTPException

from ...core.rules import TelemetryInput, evaluate_telemetry
from ...models.driver import Driver
from ...models.vehicle import Vehicle
from ...models.violation import Alert, Violation
from ...schemas.violation import AlertOut, TelemetryIn, TelemetryResult, ViolationOut
from ..deps import authed_db

router = APIRouter(tags=["telemetry"])

# Alerts are raised for these severities; LOW/MEDIUM are logged only.
ALERT_SEVERITIES = {"HIGH", "CRITICAL"}


@router.post("/telemetry", response_model=TelemetryResult)
def ingest_telemetry(payload: TelemetryIn, db=Depends(authed_db)):
    if not db.get(Driver, payload.driver_id):
        raise HTTPException(status_code=400, detail="Driver not found")
    if not db.get(Vehicle, payload.vehicle_id):
        raise HTTPException(status_code=400, detail="Vehicle not found")

    telemetry = TelemetryInput(**payload.model_dump())
    hits = evaluate_telemetry(telemetry)

    violations: list[Violation] = []
    alerts: list[Alert] = []
    for hit in hits:
        violation = Violation(
            driver_id=payload.driver_id,
            vehicle_id=payload.vehicle_id,
            trip_id=payload.trip_id,
            type=hit.violation_type,
            severity=hit.severity,
            message=hit.message,
            speed=hit.speed,
            speed_limit=hit.speed_limit,
            lat=hit.lat,
            lng=hit.lng,
        )
        db.add(violation)
        db.flush()
        violations.append(violation)
        if hit.severity in ALERT_SEVERITIES:
            alert = Alert(
                violation_id=violation.id,
                severity=hit.severity,
                message=f"[{hit.severity}] {hit.message}",
            )
            db.add(alert)
            db.flush()
            alerts.append(alert)
    db.commit()
    for v in violations:
        db.refresh(v)
    for a in alerts:
        db.refresh(a)
    return TelemetryResult(
        violations=[ViolationOut.model_validate(v) for v in violations],
        alerts=[AlertOut.model_validate(a) for a in alerts],
    )
