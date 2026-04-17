from datetime import datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.schemas.shift import ShiftUpdate


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo = None)
    return value


def get_week_bounds(reference_datetime: datetime) -> tuple[datetime, datetime]:
    week_start_date = reference_datetime.date() - timedelta(days = reference_datetime.weekday())
    week_start = datetime.combine(week_start_date, time.min)
    week_end = week_start + timedelta(days = 7)
    return week_start, week_end


def validate_schedule_exists(db: Session, schedule_id: int) -> Schedule:
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = {
                "message": "Shift validation failed",
                "errors": ["Schedule does not exist"],
            },
        )

    return schedule


def validate_shift_within_schedule(
    start_datetime: datetime,
    end_datetime: datetime,
    schedule: Schedule,
) -> list[str]:
    errors: list[str] = []

    if start_datetime.date() < schedule.start_date or end_datetime.date() > schedule.end_date:
        errors.append("Shift must be within the schedule date range")

    return errors


def validate_employee_for_assignment(
    db: Session,
    employee_id: int,
) -> Employee:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()

    if not employee:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = {
                "message": "Shift validation failed",
                "errors": ["Employee does not exist"],
            },
        )

    if employee.active is not True:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = {
                "message": "Shift validation failed",
                "errors": ["Employee is not active"],
            },
        )

    return employee


def validate_minimum_rest(
    db: Session,
    employee_id: int,
    start_datetime: datetime,
    end_datetime: datetime,
) -> list[str]:
    errors: list[str] = []

    previous_shift = (
        db.query(Shift)
        .join(Assignment, Assignment.shift_id == Shift.id)
        .filter(
            Assignment.employee_id == employee_id,
            Shift.end_datetime <= start_datetime,
        )
        .order_by(Shift.end_datetime.desc())
        .first()
    )

    if previous_shift is not None:
        minimum_allowed_start = previous_shift.end_datetime + timedelta(hours = 12)

        if start_datetime < minimum_allowed_start:
            errors.append("Minimum rest period of 12 hours has not been respected")

    next_shift = (
        db.query(Shift)
        .join(Assignment, Assignment.shift_id == Shift.id)
        .filter(
            Assignment.employee_id == employee_id,
            Shift.start_datetime >= end_datetime,
        )
        .order_by(Shift.start_datetime.asc())
        .first()
    )

    if next_shift is not None:
        minimum_allowed_end = next_shift.start_datetime - timedelta(hours = 12)

        if end_datetime > minimum_allowed_end:
            errors.append("Minimum rest period of 12 hours has not been respected")

    return errors


def validate_overlap(
    db: Session,
    employee_id: int,
    start_datetime: datetime,
    end_datetime: datetime,
) -> list[str]:
    errors: list[str] = []

    overlapping_shift = (
        db.query(Shift)
        .join(Assignment, Assignment.shift_id == Shift.id)
        .filter(
            Assignment.employee_id == employee_id,
            Shift.start_datetime < end_datetime,
            Shift.end_datetime > start_datetime,
        )
        .first()
    )

    if overlapping_shift:
        errors.append("The shift overlaps with another shift already assigned to this employee")

    return errors


def validate_weekly_hours(
    db: Session,
    employee: Employee,
    start_datetime: datetime,
    end_datetime: datetime,
) -> list[str]:
    errors: list[str] = []

    week_start, week_end = get_week_bounds(start_datetime)

    weekly_assigned_shifts = (
        db.query(Shift)
        .join(Assignment, Assignment.shift_id == Shift.id)
        .filter(
            Assignment.employee_id == employee.id,
            Shift.start_datetime >= week_start,
            Shift.start_datetime < week_end,
        )
        .all()
    )

    total_weekly_hours = 0.0

    for weekly_shift in weekly_assigned_shifts:
        total_weekly_hours += (
            weekly_shift.end_datetime - weekly_shift.start_datetime
        ).total_seconds() / 3600

    new_shift_hours = (end_datetime - start_datetime).total_seconds() / 3600
    total_weekly_hours += new_shift_hours

    if total_weekly_hours > employee.max_weekly_hours:
        errors.append("The employee has no weekly hours available")

    return errors


def get_shift_creation_errors(
    db: Session,
    start_datetime: datetime,
    end_datetime: datetime,
    schedule: Schedule,
    employee: Employee | None = None,
) -> list[str]:
    errors: list[str] = []

    errors.extend(
        validate_shift_within_schedule(
            start_datetime = start_datetime,
            end_datetime = end_datetime,
            schedule = schedule,
        )
    )

    if employee is not None:
        if employee.active is not True:
            errors.append("Employee is not active")
        else:
            errors.extend(
                validate_minimum_rest(
                    db = db,
                    employee_id = employee.id,
                    start_datetime = start_datetime,
                    end_datetime = end_datetime,
                )
            )

            errors.extend(
                validate_overlap(
                    db = db,
                    employee_id = employee.id,
                    start_datetime = start_datetime,
                    end_datetime = end_datetime,
                )
            )

            errors.extend(
                validate_weekly_hours(
                    db = db,
                    employee = employee,
                    start_datetime = start_datetime,
                    end_datetime = end_datetime,
                )
            )

    return list(dict.fromkeys(errors))


def validate_shift_creation(
    db: Session,
    start_datetime: datetime,
    end_datetime: datetime,
    schedule: Schedule,
    employee: Employee | None = None,
) -> None:
    errors = get_shift_creation_errors(
        db = db,
        start_datetime = start_datetime,
        end_datetime = end_datetime,
        schedule = schedule,
        employee = employee,
    )

    if errors:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = {
                "message": "Shift validation failed",
                "errors": errors,
            },
        )


def create_shift_with_optional_assignment(
    db: Session,
    start_datetime: datetime,
    end_datetime: datetime,
    creation_type: str,
    status_value: str,
    schedule_id: int,
    employee_id: int | None = None,
) -> Shift:
    start_datetime = normalize_datetime(start_datetime)
    end_datetime = normalize_datetime(end_datetime)

    schedule = validate_schedule_exists(db = db, schedule_id = schedule_id)

    employee = None

    if employee_id is not None:
        employee = validate_employee_for_assignment(
            db = db,
            employee_id = employee_id,
        )

    validate_shift_creation(
        db = db,
        start_datetime = start_datetime,
        end_datetime = end_datetime,
        schedule = schedule,
        employee = employee,
    )

    new_shift = Shift(
        start_datetime = start_datetime,
        end_datetime = end_datetime,
        creation_type = creation_type,
        status = status_value,
        schedule_id = schedule_id,
    )

    db.add(new_shift)
    db.flush()

    if employee is not None:
        new_assignment = Assignment(
            employee_id = employee.id,
            shift_id = new_shift.id,
        )
        db.add(new_assignment)

    db.commit()
    db.refresh(new_shift)

    return new_shift


def update_shift_with_optional_assignment(
    db: Session,
    shift_id: int,
    shift_data: ShiftUpdate,
) -> Shift:
    shift_data.start_datetime = normalize_datetime(shift_data.start_datetime)
    shift_data.end_datetime = normalize_datetime(shift_data.end_datetime)

    shift = db.query(Shift).filter(Shift.id == shift_id).first()

    if not shift:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Shift not found"
        )

    update_data = shift_data.model_dump(exclude_unset = True)

    new_start_datetime = update_data.get("start_datetime", shift.start_datetime)
    new_end_datetime = update_data.get("end_datetime", shift.end_datetime)
    new_creation_type = update_data.get("creation_type", shift.creation_type)
    new_status = update_data.get("status", shift.status)
    new_schedule_id = update_data.get("schedule_id", shift.schedule_id)

    schedule = validate_schedule_exists(db = db, schedule_id = new_schedule_id)

    current_assignment = (
        db.query(Assignment)
        .filter(Assignment.shift_id == shift.id)
        .first()
    )

    employee_id_was_sent = "employee_id" in shift_data.model_fields_set

    if employee_id_was_sent:
        requested_employee_id = shift_data.employee_id

        if requested_employee_id is None:
            employee = None
        else:
            employee = validate_employee_for_assignment(
                db = db,
                employee_id = requested_employee_id,
            )
    else:
        if current_assignment is not None:
            employee = db.query(Employee).filter(Employee.id == current_assignment.employee_id).first()
        else:
            employee = None

    errors = get_shift_creation_errors(
        db = db,
        start_datetime = new_start_datetime,
        end_datetime = new_end_datetime,
        schedule = schedule,
        employee = employee,
    )

    if current_assignment is not None and employee is not None and current_assignment.employee_id == employee.id:
        errors = [
            error for error in errors
            if error != "The shift overlaps with another shift already assigned to this employee"
        ]

    if errors:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = {
                "message": "Shift validation failed",
                "errors": list(dict.fromkeys(errors)),
            },
        )

    shift.start_datetime = new_start_datetime
    shift.end_datetime = new_end_datetime
    shift.creation_type = new_creation_type
    shift.status = new_status
    shift.schedule_id = new_schedule_id

    if employee_id_was_sent:
        if shift_data.employee_id is None:
            if current_assignment is not None:
                db.delete(current_assignment)
        else:
            if current_assignment is None:
                new_assignment = Assignment(
                    employee_id = employee.id,
                    shift_id = shift.id,
                )
                db.add(new_assignment)
            else:
                current_assignment.employee_id = employee.id

    db.commit()
    db.refresh(shift)   

    return shift     
