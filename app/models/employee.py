from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base


class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone_number = Column(String)
    max_weekly_hours = Column(Integer, nullable=False)
    active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now())