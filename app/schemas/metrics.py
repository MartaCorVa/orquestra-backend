from pydantic import BaseModel

from datetime import date

class EmployeeFairnessMetric(BaseModel):
    employee_id: int
    employee_name: str
    assigned_hours: float
    max_weekly_hours: int
    workload_percentage: float


class ScheduleFairnessResponse(BaseModel):
    schedule_id: int
    total_assigned_hours: float
    employees: list[EmployeeFairnessMetric]
    max_assigned_hours: float
    min_assigned_hours: float
    hours_gap: float


class EmployeeWorkloadMetric(BaseModel):
    employee_id: int
    employee_name: str
    assigned_hours: float
    max_weekly_hours: int
    workload_percentage: float


class WorkloadMetricsResponse(BaseModel):
    start_date: date
    end_date: date
    total_assigned_hours: float
    employees: list[EmployeeWorkloadMetric]