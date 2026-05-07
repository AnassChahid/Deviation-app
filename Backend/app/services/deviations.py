import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.deviation import Deviation, DeviationStatus
from app.models.deviation_audit import DeviationAudit, DeviationAuditAction
from app.models.deviation_type import DeviationType
from app.models.notification import Notification
from app.models.qc import QC
from app.models.user import User, UserRole
from app.models.vessel import Vessel
from app.schemas.deviation import DeviationCreate, DeviationUpdate
from app.services import notifications as notification_service

logger = logging.getLogger(__name__)


# Deviation relationship validation
def _validate_deviation_links(db: Session, deviation_type_id: int | None = None, qc_id: int | None = None) -> None:
    if deviation_type_id is not None:
        deviation_type = db.get(DeviationType, deviation_type_id)
        if not deviation_type or not deviation_type.active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active deviation type not found")

    if qc_id is not None and not db.get(QC, qc_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QC not found")


def _get_vessels(db: Session, vessel_ids: list[int] | None) -> list[Vessel]:
    if not vessel_ids:
        return []

    unique_ids = list(dict.fromkeys(vessel_ids))
    vessels = db.query(Vessel).filter(Vessel.id.in_(unique_ids)).all()
    if len(vessels) != len(unique_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more vessels not found")
    return vessels


# Deviation ownership and access helpers
def _week_of_year(value) -> str:
    return str(value.isocalendar().week)


def _can_access_all_deviations(current_user: User) -> bool:
    return current_user.role in (UserRole.admin, UserRole.superuser)


def _get_accessible_deviation(db: Session, deviation_id: int, current_user: User) -> Deviation:
    deviation = db.get(Deviation, deviation_id)
    if not deviation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deviation not found")

    if not _can_access_all_deviations(current_user) and deviation.creator_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deviation not found")
    return deviation


def _actor_name(user: User) -> str:
    return f"{user.firstName} {user.lastName}".strip() or user.email


# Audit trail helpers
def _format_value(value) -> str:
    if value is None:
        return "empty"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "empty"
    return str(value)


def _audit(
    db: Session,
    deviation_id: int,
    action: DeviationAuditAction,
    current_user: User,
    details: str | None = None,
) -> DeviationAudit:
    audit = DeviationAudit(
        deviation_id=deviation_id,
        action=action,
        actor_id=current_user.id,
        actor_name=_actor_name(current_user),
        details=details,
    )
    db.add(audit)
    return audit


def _commit_or_400(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate or invalid data") from exc


def _flush_or_400(db: Session) -> None:
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate or invalid data") from exc


# Change summary builder
def _changed_fields(deviation: Deviation, update_data: dict) -> list[str]:
    changes = []
    for field, new_value in update_data.items():
        if field == "vessel_ids":
            old_value = deviation.vessel_ids
        else:
            old_value = getattr(deviation, field)
        if old_value != new_value:
            changes.append(f"{field}: {_format_value(old_value)} -> {_format_value(new_value)}")
    return changes


# Create deviation and record audit
def create_deviation(db: Session, payload: DeviationCreate, current_user: User) -> Deviation:
    _validate_deviation_links(db, payload.deviation_type_id, payload.qc_id)
    vessels = _get_vessels(db, payload.vessel_ids)

    deviation = Deviation(
        date=payload.date,
        ts=_week_of_year(payload.date),
        shiftType=payload.shiftType,
        category=payload.category,
        duration=payload.duration,
        status=payload.status,
        description=payload.description,
        deviation_type_id=payload.deviation_type_id,
        qc_id=payload.qc_id,
        creator_id=current_user.id,
    )
    deviation.vessels = vessels
    db.add(deviation)
    _flush_or_400(db)
    _audit(db, deviation.id, DeviationAuditAction.created, current_user)
    _commit_or_400(db)
    db.refresh(deviation)

    try:
        notification_service.create_deviation_notifications(db, deviation, current_user)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to create notifications for deviation %s", deviation.id)

    return deviation


# List deviations visible to the current user
def list_deviations(db: Session, current_user: User, page: int, per_page: int) -> tuple[list[Deviation], int]:
    query = db.query(Deviation).order_by(Deviation.date.desc(), Deviation.id.desc())
    if not _can_access_all_deviations(current_user):
        query = query.filter(Deviation.creator_id == current_user.id)
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


# Read one accessible deviation
def get_deviation(db: Session, deviation_id: int, current_user: User) -> Deviation:
    return _get_accessible_deviation(db, deviation_id, current_user)


# Update deviation and record update/close audit
def update_deviation(
    db: Session,
    deviation_id: int,
    payload: DeviationUpdate,
    current_user: User,
) -> Deviation:
    deviation = _get_accessible_deviation(db, deviation_id, current_user)
    update_data = payload.model_dump(exclude_unset=True)
    changes = _changed_fields(deviation, update_data)
    old_status = deviation.status

    _validate_deviation_links(
        db,
        update_data.get("deviation_type_id"),
        update_data.get("qc_id"),
    )

    for field, value in update_data.items():
        if field == "vessel_ids":
            deviation.vessels = _get_vessels(db, value)
            continue
        setattr(deviation, field, value)

    if "date" in update_data:
        deviation.ts = _week_of_year(deviation.date)

    if changes:
        action = DeviationAuditAction.updated
        if "status" in update_data and old_status != DeviationStatus.done and deviation.status == DeviationStatus.done:
            action = DeviationAuditAction.closed
        _audit(db, deviation.id, action, current_user, "; ".join(changes))

    db.add(deviation)
    _commit_or_400(db)
    db.refresh(deviation)

    if changes:
        try:
            notification_service.create_deviation_update_notifications(db, deviation, current_user)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to create update notifications for deviation %s", deviation.id)

    return deviation


# Delete deviation and record audit before removal
def delete_deviation(db: Session, deviation_id: int, current_user: User) -> None:
    deviation = _get_accessible_deviation(db, deviation_id, current_user)
    _audit(db, deviation.id, DeviationAuditAction.deleted, current_user, f"Deleted deviation {deviation.id}")

    try:
        notification_service.create_deviation_delete_notifications(db, deviation, current_user)
        db.flush()
    except Exception:
        db.rollback()
        logger.exception("Failed to create delete notifications for deviation %s", deviation.id)
        deviation = _get_accessible_deviation(db, deviation_id, current_user)
        _audit(db, deviation.id, DeviationAuditAction.deleted, current_user, f"Deleted deviation {deviation.id}")

    db.query(Notification).filter(Notification.deviation_id == deviation.id).update(
        {"deviation_id": None},
        synchronize_session=False,
    )
    db.delete(deviation)
    _commit_or_400(db)


# List audit trail for one accessible deviation
def list_deviation_audits(db: Session, deviation_id: int, current_user: User) -> list[DeviationAudit]:
    _get_accessible_deviation(db, deviation_id, current_user)
    return (
        db.query(DeviationAudit)
        .filter(DeviationAudit.deviation_id == deviation_id)
        .order_by(DeviationAudit.created_at.desc(), DeviationAudit.id.desc())
        .all()
    )
