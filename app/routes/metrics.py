from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.models.schedule import Schedule
from app.models.user import User
from app.schemas.metrics import ScheduleFairnessResponse, WorkloadMetricsResponse
from app.services.metrics_service import calculate_schedule_fairness, calculate_workload_metrics

router = APIRouter(prefix = "/metrics", tags = ["Metrics"])


@router.get("/fairness/{schedule_id}", response_model = ScheduleFairnessResponse)
def get_schedule_fairness(
    schedule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(status_code = 404, detail = "Schedule not found")

    return calculate_schedule_fairness(db, schedule_id)


@router.get("/workload", response_model = WorkloadMetricsResponse)
def get_workload_metrics(
    start_date: date = Query(...),
    end_date: date = Query(...),
    employee_id: int | None = Query(default = None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        return calculate_workload_metrics(
            db = db,
            current_user = current_user,
            start_date = start_date,
            end_date = end_date,
            employee_id = employee_id
        )
    except ValueError as exc:
        raise HTTPException(status_code = 400, detail = str(exc))