from pydantic import BaseModel, EmailStr, ConfigDict

from app.schemas.contract import ContractCreateOnboarding, ContractResponse


class EmployeeOnboardingCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "employee"
    first_name: str
    last_name: str
    phone_number: str | None = None
    active: bool = True
    contract: ContractCreateOnboarding


class EmployeeOnboardingResponse(BaseModel):
    user_id: int
    employee_id: int
    email: EmailStr
    role: str
    must_change_password: bool
    first_name: str
    last_name: str
    phone_number: str | None = None
    active: bool
    contract: ContractResponse
    model_config = ConfigDict(from_attributes = True)