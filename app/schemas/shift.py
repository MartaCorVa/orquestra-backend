from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ShiftBase(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    creation_type: str
    status: str
    schedule_id: int

    @model_validator(mode = "after")
    def validate_datetimes(self):
        if self.end_datetime <= self.start_datetime:
            raise ValueError("End datetime must be later than start datetime")
        return self


class ShiftCreate(ShiftBase):
    employee_id: int | None = None


class ShiftUpdate(BaseModel):
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    creation_type: str | None = None
    status: str | None = None
    schedule_id: int | None = None
    employee_id: int | None = None

    @model_validator(mode = "after")
    def validate_datetimes(self):
        if (
            self.start_datetime is not None
            and self.end_datetime is not None
            and self.end_datetime <= self.start_datetime
        ):
            raise ValueError("End datetime must be later than start datetime")
        return self


class ShiftResponse(ShiftBase):
    id: int
    created_at: datetime
    employee_id: int | None = None
    employee_name: str | None = None
    model_config = ConfigDict(from_attributes = True)


class ShiftTableResponse(BaseModel):
    id: int
    start_datetime: datetime
    end_datetime: datetime
    status: str
    creation_type: str
    employee_id: int | None = None
    employee_name: str | None = None    


Weekday = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday"
]


class RecurrentShiftCreate(BaseModel):
    schedule_id: int
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    weekdays: list[Weekday] = Field(min_length=1)
    creation_type: str = "manual"
    status: str = "planned"
    employee_id: int | None = None