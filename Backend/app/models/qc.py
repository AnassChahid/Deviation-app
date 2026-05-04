from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class QC(Base):
    __tablename__ = "qcs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    qcName: Mapped[str] = mapped_column(String(120), nullable=False)

    deviations: Mapped[list["Deviation"]] = relationship(back_populates="qc")
