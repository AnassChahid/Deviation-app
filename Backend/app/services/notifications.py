from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.deviation import Deviation
from app.models.notification import Notification
from app.models.user import User, UserRole
from app.services.base import commit_or_400


def _actor_name(user: User) -> str:
    return f"{user.firstName} {user.lastName}".strip() or user.email


def _admin_recipients(db: Session) -> list[User]:
    return (
        db.query(User)
        .filter(User.active == True, User.role.in_([UserRole.admin, UserRole.superuser]))
        .all()
    )


def _add_admin_deviation_notifications(db: Session, deviation: Deviation, actor: User, title: str, action: str) -> None:
    if actor.role != UserRole.user:
        return

    actor_name = _actor_name(actor)

    for recipient in _admin_recipients(db):
        db.add(Notification(
            recipient_id=recipient.id,
            actor_id=actor.id,
            deviation_id=deviation.id,
            title=title,
            message=f"{actor_name} {action} deviation #{deviation.id}.",
        ))


def create_deviation_notifications(db: Session, deviation: Deviation, actor: User) -> None:
    _add_admin_deviation_notifications(db, deviation, actor, "New deviation created", "created")


def create_deviation_update_notifications(db: Session, deviation: Deviation, actor: User) -> None:
    _add_admin_deviation_notifications(db, deviation, actor, "Deviation updated", "updated")


def create_deviation_delete_notifications(db: Session, deviation: Deviation, actor: User) -> None:
    _add_admin_deviation_notifications(db, deviation, actor, "Deviation deleted", "deleted")


def create_user_registration_notifications(db: Session, user: User) -> None:
    actor_name = _actor_name(user)

    for recipient in _admin_recipients(db):
        db.add(Notification(
            recipient_id=recipient.id,
            actor_id=user.id,
            deviation_id=None,
            title="New account request",
            message=f"{actor_name} requested access with {user.email}.",
        ))


def list_notifications(db: Session, current_user: User) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(50)
        .all()
    )


def unread_count(db: Session, current_user: User) -> int:
    return (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id, Notification.read == False)
        .count()
    )


def mark_notification_read(db: Session, notification_id: int, current_user: User) -> Notification:
    notification = db.get(Notification, notification_id)
    if not notification or notification.recipient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notification.read = True
    return commit_or_400(db, notification)


def mark_all_read(db: Session, current_user: User) -> int:
    updated = (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id, Notification.read == False)
        .update({"read": True})
    )
    db.commit()
    return updated
