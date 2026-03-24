from sqlalchemy import Column, Integer, Date, String, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base


class Schedule(Base):
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())