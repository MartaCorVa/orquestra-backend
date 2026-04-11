import datetime as dt

from pydantic import BaseModel, ConfigDict


class ShiftBase(BaseModel):
    date: dt.date
    start_time: dt.time
    end_time: dt.time
    creation_type: str
    status: str
    schedule_id: int


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(BaseModel):
    date: dt.date | None = None
    start_time: dt.time | None = None
    end_time: dt.time | None = None
    creation_type: str | None = None
    status: str | None = None
    schedule_id: int | None = None


class ShiftResponse(ShiftBase):
    id: int
    created_at: dt.datetime
    model_config = ConfigDict(from_attributes = True)


class ShiftTableResponse(BaseModel):
    id: int
    date: dt.date
    start_time: dt.time
    end_time: dt.time
    status: str
    creation_type: str
    employee_id: int | None = None
    employee_name: str | None = None

    model_config = ConfigDict(from_attributes=True)