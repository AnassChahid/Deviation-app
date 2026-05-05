from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.qc import QCCreate, QCRead
from app.services import qcs as qc_service


router = APIRouter()


# Create QC
@router.post("", response_model=QCRead, status_code=status.HTTP_201_CREATED)
def create_qc(payload: QCCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return qc_service.create_qc(db, payload)


# List QCs
@router.get("", response_model=list[QCRead])
def list_qcs(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return qc_service.list_qcs(db)
