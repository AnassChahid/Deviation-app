from sqlalchemy.orm import Session

from app.models.qc import QC
from app.schemas.qc import QCCreate
from app.services.base import commit_or_400


# Create QC
def create_qc(db: Session, payload: QCCreate) -> QC:
    qc = QC(qcName=payload.qcName)
    return commit_or_400(db, qc)


# List QCs
def list_qcs(db: Session) -> list[QC]:
    return db.query(QC).order_by(QC.qcName).all()
