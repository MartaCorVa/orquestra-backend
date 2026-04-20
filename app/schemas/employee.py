from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.contract import ContractCreate, ContractResponse, ContractUpdate


class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    phone_number: str | None = None
    active: bool = True
    user_id: int | None = None


class EmployeeCreate(EmployeeBase):
    contract: ContractCreate


class EmployeeUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    active: bool | None = None
    user_id: int | None = None
    contract: ContractUpdate | None = None


class EmployeeResponse(EmployeeBase):
    id: int
    created_at: datetime
    contract: ContractResponse | None = None
    model_config = ConfigDict(from_attributes = True)