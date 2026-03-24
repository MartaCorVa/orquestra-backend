from sqlalchemy import Column, Integer, Date, Time, String, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base


class Shift(Base):
    __tablename__ = "shift"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    creation_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedule.id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())