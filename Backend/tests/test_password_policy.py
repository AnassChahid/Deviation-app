import os
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-thirty-two-chars")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.auth import BootstrapAdminCreate, LoginRequest, PendingUserRegister
from app.schemas.user import UserCreate, UserUpdate


STRONG_PASSWORD = "StrongPass1!"


def _account_payload(**overrides):
    payload = {
        "firstName": "Jane",
        "lastName": "Tester",
        "email": "jane.tester@apmterminals.com",
        "password": STRONG_PASSWORD,
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    "password",
    [
        "short1!",
        "lowercase1!",
        "UPPERCASE1!",
        "NoNumber!",
        "NoSymbol1",
    ],
)
def test_registration_password_must_be_strong(password):
    with pytest.raises(ValidationError):
        PendingUserRegister.model_validate(_account_payload(password=password))


def test_bootstrap_admin_accepts_strong_password():
    account = BootstrapAdminCreate.model_validate(_account_payload())

    assert account.password == STRONG_PASSWORD


def test_admin_user_create_requires_strong_password():
    with pytest.raises(ValidationError):
        UserCreate.model_validate(_account_payload(password="weakpass"))


def test_user_update_requires_strong_password_when_changed():
    with pytest.raises(ValidationError):
        UserUpdate.model_validate({"password": "weakpass"})

    update = UserUpdate.model_validate({"password": STRONG_PASSWORD})

    assert update.password == STRONG_PASSWORD


def test_login_request_does_not_apply_new_password_policy():
    login = LoginRequest.model_validate({
        "email": "jane.tester@apmterminals.com",
        "password": "old",
    })

    assert login.password == "old"
