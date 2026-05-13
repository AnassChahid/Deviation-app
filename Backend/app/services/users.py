import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import BootstrapAdminCreate, PendingUserRegister
from app.schemas.user import UserCreate, UserUpdate
from app.services.base import commit_or_400
from app.services import notifications as notification_service


logger = logging.getLogger(__name__)


# First-account bootstrap
def bootstrap_admin(db: Session, payload: BootstrapAdminCreate) -> User:
    if db.query(User).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bootstrap is disabled after first user")

    user = User(
        firstName=payload.firstName,
        lastName=payload.lastName,
        email=str(payload.email).lower(),
        password=hash_password(payload.password),
        role=UserRole.admin,
        active=True,
    )
    return commit_or_400(db, user)


# Login authentication
def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not verify_password(password, user.password):
        return None
    if not user.active:
        return None
    return user


# Admin-created user
def create_user(db: Session, payload: UserCreate) -> User:
    user = User(
        firstName=payload.firstName,
        lastName=payload.lastName,
        email=str(payload.email).lower(),
        password=hash_password(payload.password),
        role=payload.role,
        shift=payload.shift,
        active=payload.active,
    )
    return commit_or_400(db, user)


# Self-registration pending approval
def register_pending_user(db: Session, payload: PendingUserRegister) -> User:
    if not db.query(User).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Create the first administrator account before requesting user access",
        )

    user = User(
        firstName=payload.firstName,
        lastName=payload.lastName,
        email=str(payload.email).lower(),
        password=hash_password(payload.password),
        role=UserRole.user,
        shift=payload.shift,
        active=False,
    )
    user = commit_or_400(db, user)

    try:
        notification_service.create_user_registration_notifications(db, user)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to create registration notifications for user %s", user.id)

    return user


# Role assignment policy
def create_user_with_role_rules(db: Session, payload: UserCreate, current_user: User) -> User:
    if current_user.role == UserRole.admin and payload.role != UserRole.user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins can only create normal users",
        )

    if current_user.role != UserRole.superuser and payload.role == UserRole.superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the superuser can create another superuser",
        )

    return create_user(db, payload)


# User read operations
def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.id).all()


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# Role update guard
def _ensure_role_allowed(role: UserRole | None, current_user: User) -> None:
    if role is None:
        return

    if current_user.role == UserRole.admin and role != UserRole.user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins can only assign normal user role",
        )

    if current_user.role != UserRole.superuser and role == UserRole.superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the superuser can assign superuser role",
        )


# Admin user update
def update_user(db: Session, user_id: int, payload: UserUpdate, current_user: User) -> User:
    user = get_user(db, user_id)
    data = payload.model_dump(exclude_unset=True)
    _ensure_role_allowed(data.get("role"), current_user)

    if user.role == UserRole.superuser and current_user.role != UserRole.superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the superuser can update a superuser",
        )

    if "firstName" in data:
        user.firstName = data["firstName"]
    if "lastName" in data:
        user.lastName = data["lastName"]
    if "email" in data:
        user.email = str(data["email"]).lower()
    if "password" in data and data["password"]:
        user.password = hash_password(data["password"])
    if "role" in data and data["role"] is not None:
        user.role = data["role"]
    if "shift" in data:
        user.shift = data["shift"]
    if "active" in data and data["active"] is not None:
        if user.id == current_user.id and not data["active"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate your own account")
        user.active = data["active"]

    return commit_or_400(db, user)


# Admin user deletion
def delete_user(db: Session, user_id: int, current_user: User) -> None:
    user = get_user(db, user_id)
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account")
    if user.role == UserRole.superuser and current_user.role != UserRole.superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the superuser can delete a superuser",
        )

    try:
        db.delete(user)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User cannot be deleted while linked records exist",
        ) from exc
