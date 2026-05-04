from sqlalchemy import Column, ForeignKey, Integer, Table

from app.db.base import Base


deviation_vessels = Table(
    "deviation_vessels",
    Base.metadata,
    Column("deviation_id", Integer, ForeignKey("deviations.id"), primary_key=True),
    Column("vessel_id", Integer, ForeignKey("vessels.id"), primary_key=True),
)
