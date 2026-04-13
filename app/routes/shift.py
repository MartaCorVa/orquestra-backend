from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.shift import Shift
from app.models.user import User
from app.schemas.shift import ShiftCreate, ShiftResponse, ShiftTableResponse, ShiftUpdate
from app.services.shift_service import (
    create_shift_with_optional_assignment,
    get_shift_creation_errors,
    validate_employee_for_assignment,
    validate_schedule_exists,
)

router = APIRouter(prefix = "/shifts", tags = ["Shifts"])


@router.post("/", response_model = ShiftResponse, status_code = status.HTTP_201_CREATED)
def create_shift(
    shift: ShiftCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    return create_shift_with_optional_assignment(
        db = db,
        start_datetime = shift.start_datetime,
        end_datetime = shift.end_datetime,
        creation_type = shift.creation_type,
        status_value = shift.status,
        schedule_id = shift.schedule_id,
        employee_id = shift.employee_id
    )


@router.get("/", response_model = list[ShiftResponse])
def get_shifts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role == "admin":
        shifts = db.query(Shift).all()
    else:
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()

        if not employee:
            return []

        shifts = (
            db.query(Shift)
            .join(Assignment, Assignment.shift_id == Shift.id)
            .filter(Assignment.employee_id == employee.id)
            .all()
        )

    return shifts


@router.get("/table", response_model = list[ShiftTableResponse])
def get_shifts_table(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role == "admin":
        rows = (
            db.query(
                Shift.id,
                Shift.start_datetime,
                Shift.end_datetime,
                Shift.status,
                Shift.creation_type,
                Employee.id.label("employee_id"),
                (Employee.first_name + " " + Employee.last_name).label("employee_name"),
            )
            .outerjoin(Assignment, Assignment.shift_id == Shift.id)
            .outerjoin(Employee, Employee.id == Assignment.employee_id)
            .all()
        )
    else:
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()

        if not employee:
            return []

        rows = (
            db.query(
                Shift.id,
                Shift.start_datetime,
                Shift.end_datetime,
                Shift.status,
                Shift.creation_type,
                Employee.id.label("employee_id"),
                (Employee.first_name + " " + Employee.last_name).label("employee_name"),
            )
            .join(Assignment, Assignment.shift_id == Shift.id)
            .join(Employee, Employee.id == Assignment.employee_id)
            .filter(Employee.id == employee.id)
            .all()
        )

    return [
        ShiftTableResponse(
            id = row.id,
            start_datetime = row.start_datetime,
            end_datetime = row.end_datetime,
            status = row.status,
            creation_type = row.creation_type,
            employee_id = row.employee_id,
            employee_name = row.employee_name,
        )
        for row in rows
    ]


@router.get("/{shift_id}", response_model = ShiftResponse)
def get_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()

    if not shift:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Shift not found"
        )

    return shift


@router.put("/{shift_id}", response_model = ShiftResponse)
def update_shift(
    shift_id: int,
    shift_data: ShiftUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
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


@router.delete("/{shift_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()

    if not shift:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Shift not found"
        )

    assignments = db.query(Assignment).filter(Assignment.shift_id == shift.id).all()

    for assignment in assignments:
        db.delete(assignment)

    db.delete(shift)
    db.commit()