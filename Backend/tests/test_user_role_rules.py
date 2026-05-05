import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-thirty-two-chars")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.user import UserRole
from app.services import users as user_service


def test_admin_can_create_normal_user(monkeypatch):
    created_user = object()

    def fake_create_user(db, payload):
        return created_user

    monkeypatch.setattr(user_service, "create_user", fake_create_user)

    result = user_service.create_user_with_role_rules(
        db=object(),
        payload=SimpleNamespace(role=UserRole.user),
        current_user=SimpleNamespace(role=UserRole.admin),
    )

    assert result is created_user


def test_admin_cannot_create_admin_user():
    with pytest.raises(HTTPException) as exc:
        user_service.create_user_with_role_rules(
            db=object(),
            payload=SimpleNamespace(role=UserRole.admin),
            current_user=SimpleNamespace(role=UserRole.admin),
        )

    assert exc.value.status_code == 403


def test_only_superuser_can_assign_superuser_role():
    with pytest.raises(HTTPException) as exc:
        user_service._ensure_role_allowed(UserRole.superuser, SimpleNamespace(role=UserRole.admin))

    assert exc.value.status_code == 403

    user_service._ensure_role_allowed(UserRole.superuser, SimpleNamespace(role=UserRole.superuser))
