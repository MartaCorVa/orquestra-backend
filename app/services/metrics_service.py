from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.shift import Shift


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

    # Solo empleados con asignaciones en este schedule
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