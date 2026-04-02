from pydantic import BaseModel, EmailStr, ConfigDict


class EmployeeOnboardingCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "employee"
    first_name: str
    last_name: str
    phone_number: str | None = None
    max_weekly_hours: int
    active: bool = True


class EmployeeOnboardingResponse(BaseModel):
    user_id: int
    employee_id: int
    email: EmailStr
    role: str
    must_change_password: bool
    first_name: str
    last_name: str
    phone_number: str | None = None
    max_weekly_hours: int
    active: bool
    model_config = ConfigDict(from_attributes = True)