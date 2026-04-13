from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Shift(Base):
    __tablename__ = "shift"

    id = Column(Integer, primary_key=True, index=True)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    creation_type = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedule.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    schedule = relationship("Schedule", back_populates="shifts")
    assignments = relationship("Assignment", back_populates="shift")