from pydantic import BaseModel, ConfigDict, Field


class QCCreate(BaseModel):
    qcName: str = Field(min_length=1, max_length=120)


class QCRead(QCCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
