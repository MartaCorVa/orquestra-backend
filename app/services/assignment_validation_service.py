from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.shift import Shift
from app.services.scheduling_rules import get_week_bounds, validate_shift_within_schedule


def validate_minimum_rest(
    db: Session,
    employee_id: int,
    start_datetime: datetime,
    end_datetime: datetime,
    excluded_shift_id: int | None = None,
) -> list[str]:
    errors: list[str] = []

    previous_shift_query = (
        db.query(Shift)
        .join(Assignment, Assignment.shift_id == Shift.id)
        .filter(
            Assignment.employee_id == employee_id,
            Shift.end_datetime <= start_datetime,
        )
    )

    if excluded_shift_id is not None:
        previous_shift_query = previous_shift_query.filter(Shift.id != excluded_shift_id)

    previous_shift = previous_shift_query.order_by(Shift.end_datetime.desc()).first()

    if previous_shift is not None:
        minimum_allowed_start = previous_shift.end_datetime + timedelta(hours = 12)

        if start_datetime < minimum_allowed_start:
            errors.append("Minimum rest period of 12 hours has not been respected")

    next_shift_query = (
        db.query(Shift)
        .join(Assignment, Assignment.shift_id == Shift.id)
        .filter(
            Assignment.employee_id == employee_id,
            Shift.start_datetime >= end_datetime,
        )
    )

    if excluded_shift_id is not None:
        next_shift_query = next_shift_query.filter(Shift.id != excluded_shift_id)

    next_shift = next_shift_query.order_by(Shift.start_datetime.asc()).first()

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
    excluded_shift_id: int | None = None,
) -> list[str]:
    errors: list[str] = []

    overlapping_shift_query = (
        db.query(Shift)
        .join(Assignment, Assignment.shift_id == Shift.id)
        .filter(
            Assignment.employee_id == employee_id,
            Shift.start_datetime < end_datetime,
            Shift.end_datetime > start_datetime,
        )
    )

    if excluded_shift_id is not None:
        overlapping_shift_query = overlapping_shift_query.filter(Shift.id != excluded_shift_id)

    overlapping_shift = overlapping_shift_query.first()

    if overlapping_shift:
        errors.append("The shift overlaps with another shift already assigned to this employee")

    return errors


def validate_days_off(
    db: Session,
    employee_id: int,
    contract: Contract,
    start_datetime: datetime,
    excluded_shift_id: int | None = None,
) -> list[str]:
    errors: list[str] = []
    week_start, week_end = get_week_bounds(start_datetime)

    working_days_query = (
        db.query(Shift.start_datetime)
        .join(Assignment, Assignment.shift_id == Shift.id)
        .filter(
            Assignment.employee_id == employee_id,
            Shift.start_datetime >= week_start,
            Shift.start_datetime < week_end,
        )
    )

    if excluded_shift_id is not None:
        working_days_query = working_days_query.filter(Shift.id != excluded_shift_id)

    working_days = working_days_query.all()
    unique_days = {row[0].date() for row in working_days}

    max_working_days = 7 - contract.min_days_off_per_week

    if start_datetime.date() not in unique_days and len(unique_days) >= max_working_days:
        errors.append(
            f"Employee must have at least {contract.min_days_off_per_week} days off per week"
        )

    return errors


def validate_contract_weekly_hours(
    db: Session,
    employee_id: int,
    contract: Contract,
    start_datetime: datetime,
    end_datetime: datetime,
    excluded_shift_id: int | None = None,
) -> list[str]:
    errors: list[str] = []

    week_start, week_end = get_week_bounds(start_datetime)

    weekly_assigned_shifts_query = (
        db.query(Shift)
        .join(Assignment, Assignment.shift_id == Shift.id)
        .filter(
            Assignment.employee_id == employee_id,
            Shift.start_datetime >= week_start,
            Shift.start_datetime < week_end,
        )
    )

    if excluded_shift_id is not None:
        weekly_assigned_shifts_query = weekly_assigned_shifts_query.filter(Shift.id != excluded_shift_id)

    weekly_assigned_shifts = weekly_assigned_shifts_query.all()

    total_weekly_hours = 0.0

    for weekly_shift in weekly_assigned_shifts:
        total_weekly_hours += (
            weekly_shift.end_datetime - weekly_shift.start_datetime
        ).total_seconds() / 3600

    new_shift_hours = (end_datetime - start_datetime).total_seconds() / 3600
    total_weekly_hours += new_shift_hours

    if total_weekly_hours > contract.weekly_hours:
        errors.append("The employee has no weekly hours available in the active contract")

    return errors


def get_assignment_errors(
    db: Session,
    shift: Shift,
    employee: Employee,
    contract: Contract,
    excluded_shift_id: int | None = None,
) -> list[str]:
    errors: list[str] = []

    errors.extend(
        validate_shift_within_schedule(
            start_datetime = shift.start_datetime,
            end_datetime = shift.end_datetime,
            schedule = shift.schedule,
        )
    )

    errors.extend(
        validate_contract_working_day(
            contract = contract,
            start_datetime = shift.start_datetime,
        )
    )

    errors.extend(
        validate_minimum_rest(
            db = db,
            employee_id = employee.id,
            start_datetime = shift.start_datetime,
            end_datetime = shift.end_datetime,
            excluded_shift_id = excluded_shift_id,
        )
    )

    errors.extend(
        validate_overlap(
            db = db,
            employee_id = employee.id,
            start_datetime = shift.start_datetime,
            end_datetime = shift.end_datetime,
            excluded_shift_id = excluded_shift_id,
        )
    )

    errors.extend(
        validate_contract_weekly_hours(
            db = db,
            employee_id = employee.id,
            contract = contract,
            start_datetime = shift.start_datetime,
            end_datetime = shift.end_datetime,
            excluded_shift_id = excluded_shift_id,
        )
    )

    errors.extend(
        validate_days_off(
            db = db,
            employee_id = employee.id,
            contract = contract,
            start_datetime = shift.start_datetime,
            excluded_shift_id = excluded_shift_id,
        )
    )

    return list(dict.fromkeys(errors))


def get_employee_weekly_assigned_hours(
    db: Session,
    employee_id: int,
    reference_datetime: datetime,
    excluded_shift_id: int | None = None,
) -> float:
    week_start, week_end = get_week_bounds(reference_datetime)

    weekly_assigned_shifts_query = (
        db.query(Shift)
        .join(Assignment, Assignment.shift_id == Shift.id)
        .filter(
            Assignment.employee_id == employee_id,
            Shift.start_datetime >= week_start,
            Shift.start_datetime < week_end,
        )
    )

    if excluded_shift_id is not None:
        weekly_assigned_shifts_query = weekly_assigned_shifts_query.filter(Shift.id != excluded_shift_id)

    weekly_assigned_shifts = weekly_assigned_shifts_query.all()

    total_weekly_hours = 0.0

    for weekly_shift in weekly_assigned_shifts:
        total_weekly_hours += (
            weekly_shift.end_datetime - weekly_shift.start_datetime
        ).total_seconds() / 3600

    return total_weekly_hours


def get_employee_weekly_working_days(
    db: Session,
    employee_id: int,
    reference_datetime: datetime,
    excluded_shift_id: int | None = None,
) -> set:
    week_start, week_end = get_week_bounds(reference_datetime)

    working_days_query = (
        db.query(Shift.start_datetime)
        .join(Assignment, Assignment.shift_id == Shift.id)
        .filter(
            Assignment.employee_id == employee_id,
            Shift.start_datetime >= week_start,
            Shift.start_datetime < week_end,
        )
    )

    if excluded_shift_id is not None:
        working_days_query = working_days_query.filter(Shift.id != excluded_shift_id)

    working_days = working_days_query.all()

    return {row[0].date() for row in working_days}


def validate_contract_working_day(
    contract: Contract,
    start_datetime: datetime,
) -> list[str]:
    errors: list[str] = []

    weekday = start_datetime.weekday()

    allowed_by_day = {
        0: contract.work_monday,
        1: contract.work_tuesday,
        2: contract.work_wednesday,
        3: contract.work_thursday,
        4: contract.work_friday,
        5: contract.work_saturday,
        6: contract.work_sunday,
    }

    if not allowed_by_day[weekday]:
        errors.append("The employee cannot work on this day according to the active contract")

    return errors