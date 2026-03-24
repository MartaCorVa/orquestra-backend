from datetime import date, datetime

from pydantic import BaseModel


class ScheduleBase(BaseModel):
    start_date: date
    end_date: date
    status: str


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None


class ScheduleResponse(ScheduleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True