from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserShift

ALLOWED_EMAIL_DOMAIN = "apmterminals.com"
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
PASSWORD_POLICY_MESSAGE = (
    "Password must be 8-128 characters and include uppercase, lowercase, number, and symbol"
)


def validate_company_email(value: EmailStr) -> EmailStr:
    if not str(value).lower().endswith(f"@{ALLOWED_EMAIL_DOMAIN}"):
        raise ValueError(f"Email must use @{ALLOWED_EMAIL_DOMAIN}")
    return value


def validate_strong_password(value: str | None) -> str | None:
    if value is None:
        return value

    if not (PASSWORD_MIN_LENGTH <= len(value) <= PASSWORD_MAX_LENGTH):
        raise ValueError(PASSWORD_POLICY_MESSAGE)
    if not any(character.isupper() for character in value):
        raise ValueError(PASSWORD_POLICY_MESSAGE)
    if not any(character.islower() for character in value):
        raise ValueError(PASSWORD_POLICY_MESSAGE)
    if not any(character.isdigit() for character in value):
        raise ValueError(PASSWORD_POLICY_MESSAGE)
    if not any(not character.isalnum() and not character.isspace() for character in value):
        raise ValueError(PASSWORD_POLICY_MESSAGE)

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
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("email")
    @classmethod
    def email_must_be_company_domain(cls, value: EmailStr) -> EmailStr:
        return validate_company_email(value)

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        return validate_strong_password(value)


class PendingUserRegister(BaseModel):
    firstName: str = Field(min_length=1, max_length=100)
    lastName: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    shift: UserShift | None = None

    @field_validator("email")
    @classmethod
    def email_must_be_company_domain(cls, value: EmailStr) -> EmailStr:
        return validate_company_email(value)

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        return validate_strong_password(value)
