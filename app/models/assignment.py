from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    shift_id = Column(Integer, ForeignKey("shift.id"), nullable=False)
    assigned_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("employee_id", "shift_id", name="uq_employee_shift"),
    )