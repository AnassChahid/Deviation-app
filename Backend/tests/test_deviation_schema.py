import os
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-thirty-two-chars")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.deviation import DeviationCreate


def _payload(**overrides):
    payload = {
        "date": "2026-05-06",
        "shiftType": "Shift A",
        "category": "Yard",
        "duration": 30,
        "status": "Not Yet",
        "deviation_type_id": 1,
        "qc_id": 1,
    }
    payload.update(overrides)
    return payload


def test_deviation_create_requires_duration():
    payload = _payload()
    payload.pop("duration")

    with pytest.raises(ValidationError):
        DeviationCreate.model_validate(payload)


def test_deviation_create_uses_category_and_accepts_legacy_area_input():
    payload = _payload(area="Flow")
    payload.pop("category")

    deviation = DeviationCreate.model_validate(payload)

    assert deviation.category == "Flow"
    assert "area" not in deviation.model_dump()
