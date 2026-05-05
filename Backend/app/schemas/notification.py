from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    id: int
    recipient_id: int
    actor_id: int
    deviation_id: int | None
    title: str
    message: str
    read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationCount(BaseModel):
    unread: int
