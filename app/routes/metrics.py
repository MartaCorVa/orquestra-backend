from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.user import User
from app.schemas.metrics import (
    ScheduleFairnessResponse,
    WorkloadMetricsResponse,
    SummaryResponse,
    RecentScheduleResponse,
)
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
    


@router.get("/summary", response_model = SummaryResponse)
def get_metrics_summary(db: Session = Depends(get_db)):
    active_employees = db.query(Employee).filter(Employee.active == True).count()

    today = date.today()
    start_of_week = today - timedelta(days = today.weekday())
    end_of_week = start_of_week + timedelta(days = 6)

    week_start_datetime = datetime.combine(start_of_week, time.min)
    week_end_datetime = datetime.combine(end_of_week, time.max)

    weekly_shifts = (
        db.query(Shift)
        .filter(
            Shift.start_datetime >= week_start_datetime,
            Shift.start_datetime <= week_end_datetime
        )
        .count()
    )

    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.start_date <= end_of_week,
            Schedule.end_date >= start_of_week
        )
        .count()
    )

    pending_validations = db.query(Schedule).filter(Schedule.status == "draft").count()

    return {
        "active_employees": active_employees,
        "weekly_shifts": weekly_shifts,
        "schedules": schedules,
        "pending_validations": pending_validations
    }


@router.get("/recent-schedule", response_model = RecentScheduleResponse | None)
def get_recent_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    schedule = None

    if current_user.role == "admin":
        schedule = (
            db.query(Schedule)
            .order_by(Schedule.created_at.desc())
            .first()
        )
    else:
        employee = (
            db.query(Employee)
            .filter(Employee.user_id == current_user.id)
            .first()
        )

        if not employee:
            return None

        schedule = (
            db.query(Schedule)
            .join(Shift, Shift.schedule_id == Schedule.id)
            .join(Assignment, Assignment.shift_id == Shift.id)
            .filter(Assignment.employee_id == employee.id)
            .distinct()
            .order_by(Schedule.created_at.desc())
            .first()
        )

    if not schedule:
        return None

    shifts = (
        db.query(Shift)
        .filter(Shift.schedule_id == schedule.id)
        .order_by(Shift.start_datetime.asc())
        .all()
    )

    return {
        "id": schedule.id,
        "shifts": [
            {
                "date": shift.start_datetime.date(),
                "start_time": shift.start_datetime.time(),
                "end_time": shift.end_datetime.time(),
                "status": shift.status,
                "number_of_employees": (
                    db.query(Assignment)
                    .filter(Assignment.shift_id == shift.id)
                    .count()
                ),
            }
            for shift in shifts
        ]
    }