"""Violation listing with filters."""
from fastapi import APIRouter, Depends, HTTPException

from ...models.violation import SEVERITIES, VIOLATION_TYPES, Violation
from ...schemas.violation import ViolationOut
from ..deps import authed_db

router = APIRouter(prefix="/violations", tags=["violations"])


@router.get("", response_model=list[ViolationOut])
def list_violations(
    type: str | None = None,
    severity: str | None = None,
    driver_id: int | None = None,
    db=Depends(authed_db),
):
    query = db.query(Violation).order_by(Violation.id.desc())
    if type:
        if type not in VIOLATION_TYPES:
            raise HTTPException(status_code=400, detail="Invalid violation type")
        query = query.filter(Violation.type == type)
    if severity:
        if severity not in SEVERITIES:
            raise HTTPException(status_code=400, detail="Invalid severity")
        query = query.filter(Violation.severity == severity)
    if driver_id:
        query = query.filter(Violation.driver_id == driver_id)
    return query.all()


@router.get("/{violation_id}", response_model=ViolationOut)
def get_violation(violation_id: int, db=Depends(authed_db)):
    violation = db.get(Violation, violation_id)
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    return violation
