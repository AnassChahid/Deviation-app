import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-thirty-two-chars")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.notification import Notification
from app.models.user import UserRole
from app.services import notifications as notification_service


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args):
        return self

    def all(self):
        return self.rows


class FakeDb:
    def __init__(self, recipients):
        self.recipients = recipients
        self.added = []

    def query(self, model):
        assert model.__name__ == "User"
        return FakeQuery(self.recipients)

    def add(self, item):
        self.added.append(item)


def _user(user_id, role):
    return SimpleNamespace(
        id=user_id,
        role=role,
        firstName=f"User{user_id}",
        lastName="Tester",
        email=f"user{user_id}@example.com",
    )


def test_user_update_creates_admin_notifications():
    db = FakeDb([_user(10, UserRole.admin), _user(11, UserRole.superuser)])
    actor = _user(1, UserRole.user)
    deviation = SimpleNamespace(id=42)

    notification_service.create_deviation_update_notifications(db, deviation, actor)

    assert len(db.added) == 2
    assert all(isinstance(item, Notification) for item in db.added)
    assert {item.recipient_id for item in db.added} == {10, 11}
    assert all(item.title == "Deviation updated" for item in db.added)
    assert all("updated deviation #42" in item.message for item in db.added)


def test_user_delete_creates_admin_notifications():
    db = FakeDb([_user(10, UserRole.admin)])
    actor = _user(1, UserRole.user)
    deviation = SimpleNamespace(id=42)

    notification_service.create_deviation_delete_notifications(db, deviation, actor)

    assert len(db.added) == 1
    assert db.added[0].title == "Deviation deleted"
    assert "deleted deviation #42" in db.added[0].message


def test_admin_update_does_not_notify_admins():
    db = FakeDb([_user(10, UserRole.admin)])
    actor = _user(2, UserRole.admin)
    deviation = SimpleNamespace(id=42)

    notification_service.create_deviation_update_notifications(db, deviation, actor)

    assert db.added == []


def test_user_registration_creates_admin_notifications():
    db = FakeDb([_user(10, UserRole.admin), _user(11, UserRole.superuser)])
    pending_user = _user(1, UserRole.user)

    notification_service.create_user_registration_notifications(db, pending_user)

    assert len(db.added) == 2
    assert all(isinstance(item, Notification) for item in db.added)
    assert {item.recipient_id for item in db.added} == {10, 11}
    assert all(item.actor_id == pending_user.id for item in db.added)
    assert all(item.deviation_id is None for item in db.added)
    assert all(item.title == "New account request" for item in db.added)
    assert all(pending_user.email in item.message for item in db.added)
