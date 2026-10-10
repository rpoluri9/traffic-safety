"""Alert feed + acknowledgement."""
from fastapi import APIRouter, Depends, HTTPException

from ...models.violation import Alert
from ...schemas.violation import AlertOut
from ..deps import authed_db

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(unacknowledged_only: bool = False, db=Depends(authed_db)):
    query = db.query(Alert).order_by(Alert.id.desc())
    if unacknowledged_only:
        query = query.filter(Alert.acknowledged.is_(False))
    return query.all()


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(alert_id: int, db=Depends(authed_db)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    db.commit()
    db.refresh(alert)
    return alert
