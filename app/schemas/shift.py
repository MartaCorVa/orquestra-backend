import datetime

from pydantic import BaseModel, ConfigDict


class ShiftBase(BaseModel):
    date: datetime.date
    start_time: datetime.time
    end_time: datetime.time
    creation_type: str
    status: str
    schedule_id: int


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(BaseModel):
    date: datetime.date | None = None
    start_time: datetime.time | None = None
    end_time: datetime.time | None = None
    creation_type: str | None = None
    status: str | None = None
    schedule_id: int | None = None


class ShiftResponse(ShiftBase):
    id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes = True)