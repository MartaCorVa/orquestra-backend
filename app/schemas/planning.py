from pydantic import BaseModel


class GeneratePlanningRequest(BaseModel):
    schedule_id: int
    employees_per_shift: int