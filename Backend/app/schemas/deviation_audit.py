from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.deviation_audit import DeviationAuditAction


class DeviationAuditRead(BaseModel):
    id: int
    deviation_id: int
    action: DeviationAuditAction
    actor_id: int
    actor_name: str
    created_at: datetime
    details: str | None = None

    model_config = ConfigDict(from_attributes=True)
