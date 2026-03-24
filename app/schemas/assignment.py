from datetime import datetime

from pydantic import BaseModel


class AssignmentBase(BaseModel):
    employee_id: int
    shift_id: int


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    employee_id: int | None = None
    shift_id: int | None = None


class AssignmentResponse(AssignmentBase):
    id: int
    assigned_at: datetime

    class Config:
        from_attributes = True