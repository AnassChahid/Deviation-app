from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.deviation import DeviationCreate, DeviationPage, DeviationRead, DeviationUpdate
from app.schemas.deviation_audit import DeviationAuditRead
from app.services import deviations as deviation_service


router = APIRouter()


# Create deviation
@router.post("", response_model=DeviationRead, status_code=status.HTTP_201_CREATED)
def create_deviation(
    payload: DeviationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return deviation_service.create_deviation(db, payload, current_user)


# List deviations visible to current user
@router.get("", response_model=DeviationPage)
def list_deviations(
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = deviation_service.list_deviations(db, current_user, page, per_page)
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max((total + per_page - 1) // per_page, 1),
    }


# Read deviation details
@router.get("/{deviation_id}", response_model=DeviationRead)
def get_deviation(
    deviation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return deviation_service.get_deviation(db, deviation_id, current_user)


# Read deviation audit trail
@router.get("/{deviation_id}/audits", response_model=list[DeviationAuditRead])
def list_deviation_audits(
    deviation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return deviation_service.list_deviation_audits(db, deviation_id, current_user)


# Update deviation
@router.patch("/{deviation_id}", response_model=DeviationRead)
def update_deviation(
    deviation_id: int,
    payload: DeviationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return deviation_service.update_deviation(db, deviation_id, payload, current_user)


# Delete deviation
@router.delete("/{deviation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deviation(
    deviation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deviation_service.delete_deviation(db, deviation_id, current_user)
