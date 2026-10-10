"""Driver CRUD."""
from fastapi import APIRouter, Depends, HTTPException

from ...core.rules import safety_score
from ...models.driver import Driver
from ...schemas.driver import DriverCreate, DriverOut, DriverUpdate
from ..deps import authed_db

router = APIRouter(prefix="/drivers", tags=["drivers"])


def _with_score(db, driver: Driver) -> DriverOut:
    out = DriverOut.model_validate(driver)
    severities = [v.severity for v in driver.violations]
    out.safety_score = safety_score(severities)
    return out


@router.post("", response_model=DriverOut, status_code=201)
def create_driver(payload: DriverCreate, db=Depends(authed_db)):
    if db.query(Driver).filter_by(license_number=payload.license_number).first():
        raise HTTPException(status_code=400, detail="License number already exists")
    driver = Driver(**payload.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return _with_score(db, driver)


@router.get("", response_model=list[DriverOut])
def list_drivers(db=Depends(authed_db)):
    return [_with_score(db, d) for d in db.query(Driver).order_by(Driver.id).all()]


@router.get("/{driver_id}", response_model=DriverOut)
def get_driver(driver_id: int, db=Depends(authed_db)):
    driver = db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return _with_score(db, driver)


@router.put("/{driver_id}", response_model=DriverOut)
def update_driver(driver_id: int, payload: DriverUpdate, db=Depends(authed_db)):
    driver = db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(driver, key, value)
    db.commit()
    db.refresh(driver)
    return _with_score(db, driver)


@router.delete("/{driver_id}", status_code=204)
def delete_driver(driver_id: int, db=Depends(authed_db)):
    driver = db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    db.delete(driver)
    db.commit()
    return None
