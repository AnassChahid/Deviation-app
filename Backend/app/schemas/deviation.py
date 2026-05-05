from datetime import date as date_type

from pydantic import BaseModel, ConfigDict, Field

from app.models.deviation import DeviationArea, DeviationShift, DeviationStatus


class DeviationCreate(BaseModel):
    date: date_type
    shiftType: DeviationShift
    area: DeviationArea
    status: DeviationStatus = DeviationStatus.not_yet
    description: str | None = None
    deviation_type_id: int
    qc_id: int
    vessel_ids: list[int] = Field(default_factory=list)


class DeviationUpdate(BaseModel):
    date: date_type | None = None
    shiftType: DeviationShift | None = None
    area: DeviationArea | None = None
    status: DeviationStatus | None = None
    description: str | None = None
    deviation_type_id: int | None = None
    qc_id: int | None = None
    vessel_ids: list[int] | None = None


class DeviationRead(DeviationCreate):
    id: int
    ts: str
    creator_id: int
    creator_name: str

    model_config = ConfigDict(from_attributes=True)


class DeviationPage(BaseModel):
    items: list[DeviationRead]
    total: int
    page: int
    per_page: int
    pages: int
