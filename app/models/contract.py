from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, index = True)

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employee.id", ondelete = "CASCADE"),
        nullable = False,
    )

    weekly_hours: Mapped[int] = mapped_column(Integer, nullable = False)
    daily_hours: Mapped[int] = mapped_column(Integer, nullable = False)
    min_days_off_per_week: Mapped[int] = mapped_column(Integer, nullable = False, default = 2)

    work_monday: Mapped[bool] = mapped_column(Boolean, nullable = False, default = True)
    work_tuesday: Mapped[bool] = mapped_column(Boolean, nullable = False, default = True)
    work_wednesday: Mapped[bool] = mapped_column(Boolean, nullable = False, default = True)
    work_thursday: Mapped[bool] = mapped_column(Boolean, nullable = False, default = True)
    work_friday: Mapped[bool] = mapped_column(Boolean, nullable = False, default = True)
    work_saturday: Mapped[bool] = mapped_column(Boolean, nullable = False, default = False)
    work_sunday: Mapped[bool] = mapped_column(Boolean, nullable = False, default = False)

    has_fixed_schedule: Mapped[bool] = mapped_column(Boolean, nullable = False, default = False)
    preferred_start_time: Mapped[time | None] = mapped_column(Time, nullable = True)
    preferred_end_time: Mapped[time | None] = mapped_column(Time, nullable = True)

    active: Mapped[bool] = mapped_column(Boolean, nullable = False, default = True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable = True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable = True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default = func.now(),
        nullable = False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        server_default = func.now(),
        onupdate = func.now(),
        nullable = False,
    )

    employee = relationship("Employee", back_populates = "contracts")