from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User


class DeviationAuditAction(str, Enum):
    created = "created"
    updated = "updated"
    closed = "closed"
    deleted = "deleted"


class DeviationAudit(Base):
    __tablename__ = "deviation_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    deviation_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    action: Mapped[DeviationAuditAction] = mapped_column(
        SqlEnum(DeviationAuditAction, native_enum=False),
        nullable=False,
    )
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    actor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    actor: Mapped[User] = relationship()
