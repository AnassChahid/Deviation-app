from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.deviation_vessel import deviation_vessels


class Vessel(Base):
    __tablename__ = "vessels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    codeVessel: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    deviations: Mapped[list["Deviation"]] = relationship(
        secondary=deviation_vessels,
        back_populates="vessels",
    )
