from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    phone_number: str | None = None
    active: bool = True
    user_id: int | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    active: bool | None = None
    user_id: int | None = None


class EmployeeResponse(EmployeeBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes = True)