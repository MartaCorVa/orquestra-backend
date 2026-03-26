from pydantic import BaseModel, Field

class PlanningGenerateRequest(BaseModel):
    employees_per_shift: int = Field(default = 1, ge = 1)