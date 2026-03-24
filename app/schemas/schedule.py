import datetime

from pydantic import BaseModel


class ScheduleBase(BaseModel):
    start_date: datetime.date
    end_date: datetime.date
    status: str


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    status: str | None = None


class ScheduleResponse(ScheduleBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True