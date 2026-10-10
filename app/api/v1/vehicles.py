"""Vehicle CRUD."""
from fastapi import APIRouter, Depends, HTTPException

from ...models.vehicle import Vehicle
from ...schemas.vehicle import VehicleCreate, VehicleOut, VehicleUpdate
from ..deps import authed_db

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("", response_model=VehicleOut, status_code=201)
def create_vehicle(payload: VehicleCreate, db=Depends(authed_db)):
    if db.query(Vehicle).filter_by(plate_number=payload.plate_number).first():
        raise HTTPException(status_code=400, detail="Plate number already exists")
    vehicle = Vehicle(**payload.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("", response_model=list[VehicleOut])
def list_vehicles(db=Depends(authed_db)):
    return db.query(Vehicle).order_by(Vehicle.id).all()


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, db=Depends(authed_db)):
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.put("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(vehicle_id: int, payload: VehicleUpdate, db=Depends(authed_db)):
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(vehicle, key, value)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.delete("/{vehicle_id}", status_code=204)
def delete_vehicle(vehicle_id: int, db=Depends(authed_db)):
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    db.delete(vehicle)
    db.commit()
    return None
