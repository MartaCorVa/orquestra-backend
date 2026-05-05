from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.constants import SHIFT_VALIDATION_FAILED
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
                "message": SHIFT_VALIDATION_FAILED,
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
                "message": SHIFT_VALIDATION_FAILED,
                "errors": ["Employee does not exist"],
            },
        )

    if employee.active is not True:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = {
                "message": SHIFT_VALIDATION_FAILED,
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
                "message": SHIFT_VALIDATION_FAILED,
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


def get_shift_or_raise(db: Session, shift_id: int) -> Shift:
    shift = db.query(Shift).filter(Shift.id == shift_id).first()

    if not shift:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Shift not found",
        )

    return shift


def get_current_shift_assignment(db: Session, shift: Shift) -> Assignment | None:
    return (
        db.query(Assignment)
        .filter(Assignment.shift_id == shift.id)
        .first()
    )


def get_employee_for_shift_update(
    db: Session,
    shift_data: ShiftUpdate,
    current_assignment: Assignment | None,
) -> Employee | None:
    employee_id_was_sent = "employee_id" in shift_data.model_fields_set

    if employee_id_was_sent:
        if shift_data.employee_id is None:
            return None

        return validate_employee_for_assignment(
            db = db,
            employee_id = shift_data.employee_id,
        )

    if current_assignment is None:
        return None

    return (
        db.query(Employee)
        .filter(Employee.id == current_assignment.employee_id)
        .first()
    )


def validate_shift_update(
    db: Session,
    shift: Shift,
    start_datetime: datetime,
    end_datetime: datetime,
    schedule: Schedule,
    employee: Employee | None,
) -> None:
    errors = validate_shift_within_schedule(
        start_datetime = start_datetime,
        end_datetime = end_datetime,
        schedule = schedule,
    )

    if end_datetime <= start_datetime:
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
                start_datetime = start_datetime,
                end_datetime = end_datetime,
                schedule = schedule,
            )

            errors.extend(
                get_assignment_errors(
                    db = db,
                    shift = temp_shift,
                    employee = employee,
                    contract = active_contract,
                    excluded_shift_id = shift.id,
                )
            )

    if errors:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = {
                "message": SHIFT_VALIDATION_FAILED,
                "errors": list(dict.fromkeys(errors)),
            },
        )


def apply_shift_update_values(
    shift: Shift,
    update_data: dict,
) -> None:
    shift.start_datetime = update_data["start_datetime"]
    shift.end_datetime = update_data["end_datetime"]
    shift.creation_type = update_data["creation_type"]
    shift.status = update_data["status"]
    shift.schedule_id = update_data["schedule_id"]


def update_shift_assignment(
    db: Session,
    shift: Shift,
    shift_data: ShiftUpdate,
    employee: Employee | None,
    current_assignment: Assignment | None,
) -> None:
    if "employee_id" not in shift_data.model_fields_set:
        return

    if shift_data.employee_id is None:
        if current_assignment is not None:
            db.delete(current_assignment)
        return

    if current_assignment is None:
        db.add(
            Assignment(
                employee_id = employee.id,
                shift_id = shift.id,
            )
        )
        return

    current_assignment.employee_id = employee.id


def update_shift_with_optional_assignment(
    db: Session,
    shift_id: int,
    shift_data: ShiftUpdate,
) -> Shift:
    shift_data.start_datetime = normalize_datetime(shift_data.start_datetime)
    shift_data.end_datetime = normalize_datetime(shift_data.end_datetime)

    shift = get_shift_or_raise(db = db, shift_id = shift_id)

    update_data = shift_data.model_dump(exclude_unset = True)

    update_data = {
        "start_datetime": update_data.get("start_datetime", shift.start_datetime),
        "end_datetime": update_data.get("end_datetime", shift.end_datetime),
        "creation_type": update_data.get("creation_type", shift.creation_type),
        "status": update_data.get("status", shift.status),
        "schedule_id": update_data.get("schedule_id", shift.schedule_id),
    }

    schedule = validate_schedule_exists(
        db = db,
        schedule_id = update_data["schedule_id"],
    )

    current_assignment = get_current_shift_assignment(db = db, shift = shift)

    employee = get_employee_for_shift_update(
        db = db,
        shift_data = shift_data,
        current_assignment = current_assignment,
    )

    validate_shift_update(
        db = db,
        shift = shift,
        start_datetime = update_data["start_datetime"],
        end_datetime = update_data["end_datetime"],
        schedule = schedule,
        employee = employee,
    )

    apply_shift_update_values(
        shift = shift,
        update_data = update_data,
    )

    update_shift_assignment(
        db = db,
        shift = shift,
        shift_data = shift_data,
        employee = employee,
        current_assignment = current_assignment,
    )

    db.commit()
    db.refresh(shift)

    return shift