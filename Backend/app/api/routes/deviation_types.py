from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.deviation_type import DeviationTypeCreate, DeviationTypeRead, DeviationTypeUpdate
from app.services import deviation_types as deviation_type_service


router = APIRouter()


# Create deviation type
@router.post("", response_model=DeviationTypeRead, status_code=status.HTTP_201_CREATED)
def create_deviation_type(
    payload: DeviationTypeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return deviation_type_service.create_deviation_type(db, payload)


# List active deviation types for normal forms
@router.get("", response_model=list[DeviationTypeRead])
def list_deviation_types(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return deviation_type_service.list_active_deviation_types(db)


# List all deviation types for administration
@router.get("/manage", response_model=list[DeviationTypeRead])
def manage_deviation_types(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return deviation_type_service.list_deviation_types(db)


# Read deviation type
@router.get("/{deviation_type_id}", response_model=DeviationTypeRead)
def get_deviation_type(
    deviation_type_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return deviation_type_service.get_deviation_type(db, deviation_type_id)


# Update deviation type
@router.patch("/{deviation_type_id}", response_model=DeviationTypeRead)
def update_deviation_type(
    deviation_type_id: int,
    payload: DeviationTypeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return deviation_type_service.update_deviation_type(db, deviation_type_id, payload)


# Delete deviation type
@router.delete("/{deviation_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deviation_type(
    deviation_type_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    deviation_type_service.delete_deviation_type(db, deviation_type_id)
