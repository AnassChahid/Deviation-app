from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.vessel import Vessel
from app.schemas.vessel import VesselCreate, VesselUpdate
from app.services.base import commit_or_400


# Create vessel
def create_vessel(db: Session, payload: VesselCreate) -> Vessel:
    vessel = Vessel(name=payload.name, codeVessel=payload.codeVessel)
    return commit_or_400(db, vessel)


# List vessels
def list_vessels(db: Session) -> list[Vessel]:
    return db.query(Vessel).order_by(Vessel.name).all()


# Read vessel
def get_vessel(db: Session, vessel_id: int) -> Vessel:
    vessel = db.get(Vessel, vessel_id)
    if not vessel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vessel not found")
    return vessel


# Update vessel
def update_vessel(db: Session, vessel_id: int, payload: VesselUpdate) -> Vessel:
    vessel = get_vessel(db, vessel_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(vessel, field, value)
    return commit_or_400(db, vessel)
