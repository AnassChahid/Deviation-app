from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole, UserShift
from app.schemas.auth import validate_company_email


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
    password: str = Field(min_length=6, max_length=128)
    role: UserRole = UserRole.user


class UserUpdate(BaseModel):
    firstName: str | None = Field(default=None, min_length=1, max_length=100)
    lastName: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)
    role: UserRole | None = None
    shift: UserShift | None = None
    active: bool | None = None

    @field_validator("email")
    @classmethod
    def email_must_be_company_domain(cls, value: EmailStr | None) -> EmailStr | None:
        if value is None:
            return value
        return validate_company_email(value)


class UserRead(UserBase):
    id: int
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
