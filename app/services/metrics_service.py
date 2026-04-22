from datetime import date, datetime, time

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.shift import Shift
from app.models.user import User


def calculate_shift_duration_hours(shift: Shift) -> float:
    duration = shift.end_datetime - shift.start_datetime
    return duration.total_seconds() / 3600


def get_contract_for_date(
    db: Session,
    employee_id: int,
    target_date: date,
) -> Contract | None:
    return (
        db.query(Contract)
        .filter(
            Contract.employee_id == employee_id,
            Contract.start_date <= target_date,
            (Contract.end_date.is_(None) | (Contract.end_date >= target_date)),
        )
        .order_by(Contract.start_date.desc(), Contract.id.desc())
        .first()
    )


def calculate_schedule_fairness(db: Session, schedule_id: int):
    shifts = (
        db.query(Shift)
        .filter(Shift.schedule_id == schedule_id)
        .order_by(Shift.start_datetime.asc())
        .all()
    )

    if not shifts:
        return {
            "schedule_id": schedule_id,
            "total_assigned_hours": 0,
            "employees": [],
            "max_assigned_hours": 0,
            "min_assigned_hours": 0,
            "hours_gap": 0,
            "max_workload_percentage": 0,
            "min_workload_percentage": 0,
            "workload_percentage_gap": 0,
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
        employee_shifts = (
            db.query(Shift)
            .join(Assignment, Assignment.shift_id == Shift.id)
            .filter(
                Assignment.employee_id == employee.id,
                Shift.schedule_id == schedule_id,
            )
            .order_by(Shift.start_datetime.asc())
            .all()
        )

        total_hours = sum(calculate_shift_duration_hours(shift) for shift in employee_shifts)

        contract_weekly_hours_values: list[int] = []

        for shift in employee_shifts:
            contract = get_contract_for_date(
                db = db,
                employee_id = employee.id,
                target_date = shift.start_datetime.date(),
            )

            if contract is not None:
                contract_weekly_hours_values.append(contract.weekly_hours)

        reference_weekly_hours = max(contract_weekly_hours_values) if contract_weekly_hours_values else 0

        workload_percentage = (
            (total_hours / reference_weekly_hours) * 100
            if reference_weekly_hours > 0
            else 0
        )

        employee_metrics.append(
            {
                "employee_id": employee.id,
                "employee_name": f"{employee.first_name} {employee.last_name}",
                "assigned_hours": round(total_hours, 2),
                "contract_weekly_hours": reference_weekly_hours,
                "workload_percentage": round(workload_percentage, 2),
            }
        )

    hours_values = [employee["assigned_hours"] for employee in employee_metrics] if employee_metrics else [0]
    percentage_values = [employee["workload_percentage"] for employee in employee_metrics] if employee_metrics else [0]

    max_assigned_hours = max(hours_values)
    min_assigned_hours = min(hours_values)
    hours_gap = max_assigned_hours - min_assigned_hours
    total_assigned_hours = sum(hours_values)

    max_workload_percentage = max(percentage_values)
    min_workload_percentage = min(percentage_values)
    workload_percentage_gap = max_workload_percentage - min_workload_percentage

    return {
        "schedule_id": schedule_id,
        "total_assigned_hours": round(total_assigned_hours, 2),
        "employees": employee_metrics,
        "max_assigned_hours": round(max_assigned_hours, 2),
        "min_assigned_hours": round(min_assigned_hours, 2),
        "hours_gap": round(hours_gap, 2),
        "max_workload_percentage": round(max_workload_percentage, 2),
        "min_workload_percentage": round(min_workload_percentage, 2),
        "workload_percentage_gap": round(workload_percentage_gap, 2)
    }


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

    range_start = datetime.combine(start_date, time.min)
    range_end = datetime.combine(end_date, time.max)

    for employee in employees:
        shifts = (
            db.query(Shift)
            .join(Assignment, Assignment.shift_id == Shift.id)
            .filter(
                Assignment.employee_id == employee.id,
                Shift.start_datetime >= range_start,
                Shift.start_datetime <= range_end,
            )
            .order_by(Shift.start_datetime.asc())
            .all()
        )

        total_hours = sum(calculate_shift_duration_hours(shift) for shift in shifts)

        contract_weekly_hours_values: list[int] = []

        for shift in shifts:
            contract = get_contract_for_date(
                db = db,
                employee_id = employee.id,
                target_date = shift.start_datetime.date()
            )

            if contract is not None:
                contract_weekly_hours_values.append(contract.weekly_hours)

        reference_weekly_hours = max(contract_weekly_hours_values) if contract_weekly_hours_values else 0

        workload_percentage = (
            (total_hours / reference_weekly_hours) * 100
            if reference_weekly_hours > 0
            else 0
        )

        employee_metrics.append(
            {
                "employee_id": employee.id,
                "employee_name": f"{employee.first_name} {employee.last_name}",
                "assigned_hours": round(total_hours, 2),
                "contract_weekly_hours": reference_weekly_hours,
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