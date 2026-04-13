from pydantic import BaseModel


class GeneratePlanningRequest(BaseModel):
    employees_per_shift: int