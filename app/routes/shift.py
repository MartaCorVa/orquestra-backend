from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.shift import Shift
from app.models.schedule import Schedule
from app.models.user import User
from app.schemas.shift import ShiftCreate, ShiftResponse, ShiftTableResponse, ShiftUpdate

router = APIRouter(prefix = "/shifts", tags = ["Shifts"])


@router.post("/", response_model = ShiftResponse, status_code = status.HTTP_201_CREATED)
def create_shift(
    shift: ShiftCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    schedule = db.query(Schedule).filter(Schedule.id == shift.schedule_id).first()

    if not schedule:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Schedule does not exist"
        )

    new_shift = Shift(
        date = shift.date,
        start_time = shift.start_time,
        end_time = shift.end_time,
        creation_type = shift.creation_type,
        status = shift.status,
        schedule_id = shift.schedule_id
    )

    db.add(new_shift)
    db.commit()
    db.refresh(new_shift)

    return new_shift


@router.get("/", response_model=list[ShiftResponse])
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


@router.get("/table", response_model=list[ShiftTableResponse])
def get_shifts_table(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role == "admin":
        rows = (
            db.query(
                Shift.id,
                Shift.date,
                Shift.start_time,
                Shift.end_time,
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
                Shift.date,
                Shift.start_time,
                Shift.end_time,
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
            date = row.date,
            start_time = row.start_time,
            end_time = row.end_time,
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

    for field, value in update_data.items():
        setattr(shift, field, value)

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

    db.delete(shift)
    db.commit()