from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.models.assignment import Assignment
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.shift import Shift
from app.models.user import User
from app.schemas.shift import (
    RecurrentShiftCreate,
    ShiftCreate,
    ShiftResponse,
    ShiftTableResponse,
    ShiftUpdate,
)
from app.services.assignment_validation_service import get_assignment_errors
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


def get_active_contract_for_employee(
    db: Session,
    employee_id: int,
) -> Contract | None:
    return (
        db.query(Contract)
        .filter(
            Contract.employee_id == employee_id,
            Contract.active == True,
        )
        .first()
    )


def can_employee_work_on_weekday(
    contract: Contract,
    weekday: int,
) -> bool:
    weekday_permissions = {
        0: contract.work_monday,
        1: contract.work_tuesday,
        2: contract.work_wednesday,
        3: contract.work_thursday,
        4: contract.work_friday,
        5: contract.work_saturday,
        6: contract.work_sunday,
    }

    return weekday_permissions[weekday]


@router.post("/", response_model = ShiftResponse, status_code = status.HTTP_201_CREATED)
def create_shift(
    shift: ShiftCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_user)]
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
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
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
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
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


@router.post("/recurrent", response_model = list[ShiftResponse], status_code = status.HTTP_201_CREATED)
def create_recurrent_shifts(
    payload: RecurrentShiftCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_user)]
):
    if payload.start_date > payload.end_date:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Start date cannot be later than end date"
        )

    if payload.start_time >= payload.end_time:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "End time must be later than start time"
        )

    weekday_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    selected_weekdays = {weekday_map[weekday] for weekday in payload.weekdays}

    active_contract = None

    if payload.employee_id is not None:
        employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()

        if not employee:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Employee does not exist"
            )

        active_contract = get_active_contract_for_employee(
            db = db,
            employee_id = payload.employee_id,
        )

        if active_contract is None:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Employee does not have an active contract"
            )

        invalid_weekdays = [
            weekday
            for weekday in selected_weekdays
            if not can_employee_work_on_weekday(active_contract, weekday)
        ]

        if invalid_weekdays:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Selected shifts do not respect the employee active contract working days"
            )

    affected_shifts: list[Shift] = []
    current_date = payload.start_date

    while current_date <= payload.end_date:
        if current_date.weekday() in selected_weekdays:
            start_datetime = datetime.combine(current_date, payload.start_time)
            end_datetime = datetime.combine(current_date, payload.end_time)

            existing_shift = (
                db.query(Shift)
                .filter(
                    Shift.schedule_id == payload.schedule_id,
                    Shift.start_datetime == start_datetime,
                    Shift.end_datetime == end_datetime
                )
                .first()
            )

            if existing_shift:
                if payload.employee_id is not None:
                    existing_assignment = (
                        db.query(Assignment)
                        .filter(
                            Assignment.shift_id == existing_shift.id,
                            Assignment.employee_id == payload.employee_id
                        )
                        .first()
                    )
            
                    if existing_assignment is None:
                        assignment_errors = get_assignment_errors(
                            db = db,
                            shift = existing_shift,
                            employee = employee,
                            contract = active_contract
                        )
            
                        if assignment_errors:
                            raise HTTPException(
                                status_code = status.HTTP_400_BAD_REQUEST,
                                detail = {
                                    "message": "Shift validation failed",
                                    "errors": assignment_errors
                                },
                            )
            
                        assignment = Assignment(
                            shift_id=existing_shift.id,
                            employee_id=payload.employee_id,
                        )
                        db.add(assignment)
            
                affected_shifts.append(existing_shift)
            else:
                new_shift = create_shift_with_optional_assignment(
                    db=db,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    creation_type=payload.creation_type,
                    status_value=payload.status,
                    schedule_id=payload.schedule_id,
                    employee_id=payload.employee_id,
                )

                affected_shifts.append(new_shift)

        current_date += timedelta(days = 1)

    if not affected_shifts:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "No shifts were created or updated because no selected weekdays match the date range",
        )

    db.commit()

    return [
        build_shift_response(db = db, shift = shift)
        for shift in affected_shifts
    ]


@router.get("/{shift_id}", response_model = ShiftResponse)
def get_shift(
    shift_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)]
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
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_user)]
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
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_user)]
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