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
    update_shift_with_optional_assignment,
)

router = APIRouter(prefix = "/shifts", tags = ["Shifts"])


def build_shift_response(db: Session, shift: Shift) -> ShiftResponse:
    row = (
        db.query(
            Employee.id.label("employee_id"),
            (Employee.first_name + " " + Employee.last_name).label("employee_name"),
        )
        .join(Assignment, Assignment.employee_id == Employee.id)
        .filter(Assignment.shift_id == shift.id)
        .first()
    )

    return ShiftResponse(
        id = shift.id,
        start_datetime = shift.start_datetime,
        end_datetime = shift.end_datetime,
        creation_type = shift.creation_type,
        status = shift.status,
        schedule_id = shift.schedule_id,
        created_at = shift.created_at,
        employee_id = row.employee_id if row is not None else None,
        employee_name = row.employee_name if row is not None else None,
    )


@router.post("/", response_model = ShiftResponse, status_code = status.HTTP_201_CREATED)
def create_shift(
    shift: ShiftCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    new_shift = create_shift_with_optional_assignment(
        db = db,
        start_datetime = shift.start_datetime,
        end_datetime = shift.end_datetime,
        creation_type = shift.creation_type,
        status_value = shift.status,
        schedule_id = shift.schedule_id,
        employee_id = shift.employee_id
    )

    return build_shift_response(db = db, shift = new_shift)


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

    return [build_shift_response(db = db, shift = shift) for shift in shifts]


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

    return build_shift_response(db = db, shift = shift)


@router.put("/{shift_id}", response_model = ShiftResponse)
def update_shift(
    shift_id: int,
    shift_data: ShiftUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    updated_shift = update_shift_with_optional_assignment(
        db = db,
        shift_id = shift_id,
        shift_data = shift_data
    )  

    return build_shift_response(db = db, shift = updated_shift)


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