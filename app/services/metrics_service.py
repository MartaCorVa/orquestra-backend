from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.shift import Shift
from app.models.user import User

from datetime import date
from datetime import datetime


def calculate_schedule_fairness(db: Session, schedule_id: int):
    shifts = db.query(Shift).filter(Shift.schedule_id == schedule_id).all()

    if not shifts:
        return {
            "schedule_id": schedule_id,
            "total_assigned_hours": 0,
            "employees": [],
            "max_assigned_hours": 0,
            "min_assigned_hours": 0,
            "hours_gap": 0
        }

    shift_ids = [shift.id for shift in shifts]

    employees = (
        db.query(Employee)
        .join(Assignment, Assignment.employee_id == Employee.id)
        .filter(Assignment.shift_id.in_(shift_ids))
        .distinct()
        .all()
    )

    employee_metrics = []

    for employee in employees:
        assignments = (
            db.query(Assignment)
            .join(Shift, Assignment.shift_id == Shift.id)
            .filter(
                Assignment.employee_id == employee.id,
                Shift.schedule_id == schedule_id
            )
            .all()
        )

        total_hours = 0

        for assignment in assignments:
            shift = db.query(Shift).filter(Shift.id == assignment.shift_id).first()

            duration = (
                shift.end_time.hour + shift.end_time.minute / 60
                - shift.start_time.hour - shift.start_time.minute / 60
            )

            total_hours += duration

        workload_percentage = (
            (total_hours / employee.max_weekly_hours) * 100
            if employee.max_weekly_hours > 0
            else 0
        )

        employee_metrics.append(
            {
                "employee_id": employee.id,
                "employee_name": f"{employee.first_name} {employee.last_name}",
                "assigned_hours": round(total_hours, 2),
                "max_weekly_hours": employee.max_weekly_hours,
                "workload_percentage": round(workload_percentage, 2)
            }
        )

    hours_values = [e["assigned_hours"] for e in employee_metrics] if employee_metrics else [0]

    max_assigned_hours = max(hours_values)
    min_assigned_hours = min(hours_values)
    hours_gap = max_assigned_hours - min_assigned_hours
    total_assigned_hours = sum(hours_values)

    return {
        "schedule_id": schedule_id,
        "total_assigned_hours": round(total_assigned_hours, 2),
        "employees": employee_metrics,
        "max_assigned_hours": round(max_assigned_hours, 2),
        "min_assigned_hours": round(min_assigned_hours, 2),
        "hours_gap": round(hours_gap, 2)
    }


def calculate_shift_duration_hours(shift: Shift) -> float:
    start_datetime = datetime.combine(shift.date, shift.start_time)
    end_datetime = datetime.combine(shift.date, shift.end_time)

    duration = end_datetime - start_datetime

    return duration.total_seconds() / 3600


def calculate_workload_metrics(
    db: Session,
    current_user: User,
    start_date: date,
    end_date: date,
    employee_id: int | None = None
):
    if start_date > end_date:
        raise ValueError("Start date cannot be later than end date")

    employee_query = db.query(Employee).filter(Employee.active == True)

    if current_user.role == "admin":
        if employee_id is not None:
            employee_query = employee_query.filter(Employee.id == employee_id)
    else:
        employee_query = employee_query.filter(Employee.user_id == current_user.id)

    employees = employee_query.all()

    employee_metrics = []

    for employee in employees:
        shifts = (
            db.query(Shift)
            .join(Assignment, Assignment.shift_id == Shift.id)
            .filter(
                Assignment.employee_id == employee.id,
                Shift.date >= start_date,
                Shift.date <= end_date
            )
            .all()
        )

        total_hours = sum(calculate_shift_duration_hours(shift) for shift in shifts)

        workload_percentage = (
            (total_hours / employee.max_weekly_hours) * 100
            if employee.max_weekly_hours > 0
            else 0
        )

        employee_metrics.append(
            {
                "employee_id": employee.id,
                "employee_name": f"{employee.first_name} {employee.last_name}",
                "assigned_hours": round(total_hours, 2),
                "max_weekly_hours": employee.max_weekly_hours,
                "workload_percentage": round(workload_percentage, 2)
            }
        )

    total_assigned_hours = round(
        sum(employee["assigned_hours"] for employee in employee_metrics),
        2
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_assigned_hours": total_assigned_hours,
        "employees": employee_metrics
    }