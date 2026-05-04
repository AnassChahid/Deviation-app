from pydantic import BaseModel, ConfigDict, Field


class VesselCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    codeVessel: str = Field(min_length=1, max_length=80)


class VesselUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    codeVessel: str | None = Field(default=None, min_length=1, max_length=80)


class VesselRead(VesselCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
