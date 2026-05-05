from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.vessel import VesselCreate, VesselRead, VesselUpdate
from app.services import vessels as vessel_service


router = APIRouter()


# Create vessel
@router.post("", response_model=VesselRead, status_code=status.HTTP_201_CREATED)
def create_vessel(payload: VesselCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return vessel_service.create_vessel(db, payload)


# List vessels
@router.get("", response_model=list[VesselRead])
def list_vessels(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return vessel_service.list_vessels(db)


# Read vessel
@router.get("/{vessel_id}", response_model=VesselRead)
def get_vessel(vessel_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return vessel_service.get_vessel(db, vessel_id)


# Update vessel
@router.patch("/{vessel_id}", response_model=VesselRead)
def update_vessel(
    vessel_id: int,
    payload: VesselUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return vessel_service.update_vessel(db, vessel_id, payload)
