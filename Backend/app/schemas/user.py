from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole, UserShift
from app.schemas.auth import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    validate_company_email,
    validate_strong_password,
)


class UserBase(BaseModel):
    firstName: str = Field(min_length=1, max_length=100)
    lastName: str = Field(min_length=1, max_length=100)
    email: EmailStr
    shift: UserShift | None = None
    active: bool = True

    @field_validator("email")
    @classmethod
    def email_must_be_company_domain(cls, value: EmailStr) -> EmailStr:
        return validate_company_email(value)


class UserCreate(UserBase):
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    role: UserRole = UserRole.user

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        return validate_strong_password(value)


class UserUpdate(BaseModel):
    firstName: str | None = Field(default=None, min_length=1, max_length=100)
    lastName: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    role: UserRole | None = None
    shift: UserShift | None = None
    active: bool | None = None

    @field_validator("email")
    @classmethod
    def email_must_be_company_domain(cls, value: EmailStr | None) -> EmailStr | None:
        if value is None:
            return value
        return validate_company_email(value)

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str | None) -> str | None:
        return validate_strong_password(value)


class UserRead(UserBase):
    id: int
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
