from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import users as user_service


router = APIRouter()


# Create user
@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return user_service.create_user_with_role_rules(db, payload, current_user)


# List users
@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return user_service.list_users(db)


# Read user
@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return user_service.get_user(db, user_id)


# Update user
@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return user_service.update_user(db, user_id, payload, current_user)


# Delete user
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    user_service.delete_user(db, user_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
