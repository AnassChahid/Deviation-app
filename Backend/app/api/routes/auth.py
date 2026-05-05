from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import BootstrapAdminCreate, LoginRequest, PendingUserRegister, Token
from app.schemas.user import UserRead
from app.services import users as user_service


router = APIRouter()


# First account bootstrap endpoint
@router.post("/bootstrap-admin", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def bootstrap_admin(payload: BootstrapAdminCreate, db: Session = Depends(get_db)):
    return user_service.bootstrap_admin(db, payload)


# Pending self-registration endpoint
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: PendingUserRegister, db: Session = Depends(get_db)):
    return user_service.register_pending_user(db, payload)


# JSON login endpoint used by the frontend
@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = user_service.authenticate_user(db, str(payload.email), payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return Token(access_token=create_access_token(user.email))


# OAuth2-compatible token endpoint
@router.post("/token", response_model=Token)
def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return Token(access_token=create_access_token(user.email))


# Current authenticated user endpoint
@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
