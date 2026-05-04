from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserShift

ALLOWED_EMAIL_DOMAIN = "apmterminals.com"


def validate_company_email(value: EmailStr) -> EmailStr:
    if not str(value).lower().endswith(f"@{ALLOWED_EMAIL_DOMAIN}"):
        raise ValueError(f"Email must use @{ALLOWED_EMAIL_DOMAIN}")
    return value


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class BootstrapAdminCreate(BaseModel):
    firstName: str = Field(min_length=1, max_length=100)
    lastName: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def email_must_be_company_domain(cls, value: EmailStr) -> EmailStr:
        return validate_company_email(value)


class PendingUserRegister(BaseModel):
    firstName: str = Field(min_length=1, max_length=100)
    lastName: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    shift: UserShift | None = None

    @field_validator("email")
    @classmethod
    def email_must_be_company_domain(cls, value: EmailStr) -> EmailStr:
        return validate_company_email(value)
