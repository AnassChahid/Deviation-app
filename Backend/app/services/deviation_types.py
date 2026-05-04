import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.deviation_type import DeviationType
from app.schemas.deviation_type import DeviationTypeCreate, DeviationTypeUpdate
from app.services.base import commit_or_400

logger = logging.getLogger("app.deviation_types.service")


def create_deviation_type(db: Session, payload: DeviationTypeCreate) -> DeviationType:
    deviation_type = DeviationType(name=payload.name, active=payload.active)
    created = commit_or_400(db, deviation_type)
    logger.info("created deviation_type id=%s name=%r active=%s", created.id, created.name, created.active)
    return created


def list_active_deviation_types(db: Session) -> list[DeviationType]:
    rows = db.query(DeviationType).filter(DeviationType.active == True).order_by(DeviationType.name).all()
    logger.info("list_active_deviation_types rows=%s values=%s", len(rows), [(row.id, row.name, row.active) for row in rows])
    return rows


def list_deviation_types(db: Session) -> list[DeviationType]:
    rows = db.query(DeviationType).order_by(DeviationType.name).all()
    logger.info("list_deviation_types rows=%s values=%s", len(rows), [(row.id, row.name, row.active) for row in rows])
    return rows


def get_deviation_type(db: Session, deviation_type_id: int) -> DeviationType:
    deviation_type = db.get(DeviationType, deviation_type_id)
    if not deviation_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deviation type not found")
    return deviation_type


def update_deviation_type(db: Session, deviation_type_id: int, payload: DeviationTypeUpdate) -> DeviationType:
    deviation_type = get_deviation_type(db, deviation_type_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(deviation_type, field, value)
    return commit_or_400(db, deviation_type)


def delete_deviation_type(db: Session, deviation_type_id: int) -> None:
    deviation_type = get_deviation_type(db, deviation_type_id)
    try:
        db.delete(deviation_type)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deviation type is used by deviations and cannot be deleted",
        ) from exc
