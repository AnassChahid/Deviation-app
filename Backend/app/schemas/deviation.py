from datetime import date as date_type

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.deviation import DeviationCategory, DeviationShift, DeviationStatus


class DeviationCreate(BaseModel):
    date: date_type
    shiftType: DeviationShift
    category: DeviationCategory = Field(validation_alias=AliasChoices("category", "area"))
    duration: int = Field(ge=0)
    status: DeviationStatus = DeviationStatus.not_yet
    description: str | None = None
    deviation_type_id: int
    qc_id: int
    vessel_ids: list[int] = Field(default_factory=list)


class DeviationUpdate(BaseModel):
    date: date_type | None = None
    shiftType: DeviationShift | None = None
    category: DeviationCategory | None = Field(default=None, validation_alias=AliasChoices("category", "area"))
    duration: int | None = Field(default=None, ge=0)
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
