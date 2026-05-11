from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict


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
    model_config = ConfigDict(from_attributes = True)


class ScheduleDetailEmployeeResponse(BaseModel):
    id: int
    first_name: str
    last_name: str


class ScheduleDetailAssignmentResponse(BaseModel):
    id: int
    employee: ScheduleDetailEmployeeResponse


class ScheduleDetailShiftResponse(BaseModel):
    id: int
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    status: str
    assignments: list[ScheduleDetailAssignmentResponse]


class ScheduleDetailResponse(BaseModel):
    id: int
    start_date: date
    end_date: date
    status: str
    shifts: list[ScheduleDetailShiftResponse]