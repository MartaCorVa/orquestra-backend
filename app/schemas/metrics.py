from pydantic import BaseModel


class EmployeeWorkloadMetric(BaseModel):
    employee_id: int
    employee_name: str
    assigned_hours: float
    max_weekly_hours: int
    workload_percentage: float


class ScheduleFairnessResponse(BaseModel):
    schedule_id: int
    total_assigned_hours: float
    employees: list[EmployeeWorkloadMetric]
    max_assigned_hours: float
    min_assigned_hours: float
    hours_gap: float