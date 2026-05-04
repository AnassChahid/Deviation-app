from pydantic import BaseModel, ConfigDict, Field


class DeviationTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    active: bool = True


class DeviationTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    active: bool | None = None


class DeviationTypeRead(DeviationTypeCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
