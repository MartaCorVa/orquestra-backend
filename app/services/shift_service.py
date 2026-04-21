from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.schemas.shift import ShiftUpdate
from app.services.assignment_validation_service import get_assignment_errors
from app.services.scheduling_rules import validate_shift_within_schedule


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo = None)
    return value


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


def validate_shift_creation(
    db: Session,
    start_datetime: datetime,
    end_datetime: datetime,
    schedule: Schedule,
    employee: Employee | None = None,
) -> None:
    errors: list[str] = []

    errors.extend(
        validate_shift_within_schedule(
            start_datetime = start_datetime,
            end_datetime = end_datetime,
            schedule = schedule,
        )
    )

    if end_datetime <= start_datetime:
        errors.append("End datetime must be later than start datetime")

    if employee is not None:
        if employee.active is not True:
            errors.append("Employee is not active")
        else:
            active_contract = next(
                (contract for contract in employee.contracts if contract.active),
                None,
            )

            if active_contract is None:
                errors.append("Employee does not have an active contract")
            else:
                shift = Shift(
                    start_datetime = start_datetime,
                    end_datetime = end_datetime,
                    schedule = schedule,
                )

                errors.extend(
                    get_assignment_errors(
                        db = db,
                        shift = shift,
                        employee = employee,
                        contract = active_contract,
                    )
                )

    if errors:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = {
                "message": "Shift validation failed",
                "errors": list(dict.fromkeys(errors)),
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

    errors: list[str] = []

    errors.extend(
        validate_shift_within_schedule(
            start_datetime = new_start_datetime,
            end_datetime = new_end_datetime,
            schedule = schedule,
        )
    )

    if new_end_datetime <= new_start_datetime:
        errors.append("End datetime must be later than start datetime")

    if employee is not None:
        active_contract = next(
            (contract for contract in employee.contracts if contract.active),
            None,
        )

        if active_contract is None:
            errors.append("Employee does not have an active contract")
        else:
            temp_shift = Shift(
                id = shift.id,
                start_datetime = new_start_datetime,
                end_datetime = new_end_datetime,
                schedule = schedule,
            )

            assignment_errors = get_assignment_errors(
                db = db,
                shift = temp_shift,
                employee = employee,
                contract = active_contract,
                excluded_shift_id = shift.id,
            )

            errors.extend(assignment_errors)

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