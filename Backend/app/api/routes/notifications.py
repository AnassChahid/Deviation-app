from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationCount, NotificationRead
from app.services import notifications as notification_service


router = APIRouter()


@router.get("", response_model=list[NotificationRead])
def list_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return notification_service.list_notifications(db, current_user)


@router.get("/unread-count", response_model=NotificationCount)
def unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"unread": notification_service.unread_count(db, current_user)}


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return notification_service.mark_notification_read(db, notification_id, current_user)


@router.patch("/read-all", response_model=NotificationCount)
def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"unread": notification_service.mark_all_read(db, current_user)}
