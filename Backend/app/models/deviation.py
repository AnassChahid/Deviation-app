from enum import Enum

from sqlalchemy import Date, Enum as SqlEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.deviation_type import DeviationType
from app.models.deviation_vessel import deviation_vessels
from app.models.qc import QC
from app.models.user import User
from app.models.vessel import Vessel


class DeviationShift(str, Enum):
    shift_a = "Shift A"
    shift_b = "Shift B"
    shift_c = "Shift C"
    shift_d = "Shift D"


class DeviationCategory(str, Enum):
    equipments = "Equipments"
    flow = "Flow"
    planning = "Planning"
    yard = "Yard"
    human = "Human"
    others = "Others"


class DeviationStatus(str, Enum):
    done = "Done"
    on_going = "On going"
    not_yet = "Not Yet"


def _enum_values(enum):
    return [item.value for item in enum]


class Deviation(Base):
    __tablename__ = "deviations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    ts: Mapped[str] = mapped_column(String(120), nullable=False)
    shiftType: Mapped[DeviationShift] = mapped_column(
        SqlEnum(DeviationShift, native_enum=False, values_callable=_enum_values),
        nullable=False,
    )
    category: Mapped[DeviationCategory] = mapped_column(
        SqlEnum(DeviationCategory, native_enum=False, values_callable=_enum_values),
        nullable=False,
        default=DeviationCategory.yard,
    )
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[DeviationStatus] = mapped_column(
        SqlEnum(DeviationStatus, native_enum=False, values_callable=_enum_values),
        nullable=False,
        default=DeviationStatus.not_yet,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    deviation_type_id: Mapped[int] = mapped_column(ForeignKey("deviation_types.id"), nullable=False)
    qc_id: Mapped[int] = mapped_column(ForeignKey("qcs.id"), nullable=False)

    creator: Mapped[User] = relationship(back_populates="deviations")
    deviation_type: Mapped[DeviationType] = relationship(back_populates="deviations")
    qc: Mapped[QC] = relationship(back_populates="deviations")
    vessels: Mapped[list[Vessel]] = relationship(
        secondary=deviation_vessels,
        back_populates="deviations",
    )

    @property
    def vessel_ids(self) -> list[int]:
        return [vessel.id for vessel in self.vessels]

    @property
    def creator_name(self) -> str:
        if not self.creator:
            return ""
        return f"{self.creator.firstName} {self.creator.lastName}".strip()
