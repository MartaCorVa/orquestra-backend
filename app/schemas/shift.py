from datetime import date, datetime, time

from pydantic import BaseModel


class ShiftBase(BaseModel):
    date: date
    start_time: time
    end_time: time
    creation_type: str
    status: str
    schedule_id: int


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(BaseModel):
    date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    creation_type: str | None = None
    status: str | None = None
    schedule_id: int | None = None


class ShiftResponse(ShiftBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True