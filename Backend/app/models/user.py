from enum import Enum

from sqlalchemy import Boolean, Enum as SqlEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, Enum):
    superuser = "superuser"
    admin = "admin"
    user = "user"


class UserShift(str, Enum):
    shift_a = "Shift A"
    shift_b = "Shift B"
    shift_c = "Shift C"
    shift_d = "Shift D"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), default=UserRole.user, nullable=False)
    firstName: Mapped[str] = mapped_column(String(100), nullable=False)
    lastName: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    shift: Mapped[UserShift | None] = mapped_column(SqlEnum(UserShift, native_enum=False), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deviations: Mapped[list["Deviation"]] = relationship(back_populates="creator")
