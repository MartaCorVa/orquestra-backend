from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.constants import SCHEDULE_NOT_FOUND
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.user import User
from app.schemas.schedule import ScheduleCreate, ScheduleDetailResponse, ScheduleResponse, ScheduleUpdate

router = APIRouter(prefix = "/schedules", tags = ["Schedules"])


@router.post("/", response_model = ScheduleResponse, status_code = status.HTTP_201_CREATED)
def create_schedule(
    schedule: ScheduleCreate, 
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_user)]
):
    new_schedule = Schedule(
        start_date = schedule.start_date,
        end_date = schedule.end_date,
        status = schedule.status
    )

    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)

    return new_schedule


@router.get("/", response_model=list[ScheduleResponse])
def get_schedules(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    if current_user.role == "admin":
        schedules = db.query(Schedule).all()
    else:
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()

        if not employee:
            return []

        schedules = (
            db.query(Schedule)
            .join(Shift, Shift.schedule_id == Schedule.id)
            .join(Assignment, Assignment.shift_id == Shift.id)
            .filter(Assignment.employee_id == employee.id)
            .distinct()
            .all()
        )

    return schedules


@router.get(
    "/{schedule_id}",
    response_model=ScheduleDetailResponse,
    responses = {
        404: {"description": SCHEDULE_NOT_FOUND}
    }
)
def get_schedule_by_id(
    schedule_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(
            status_code = 404,
            detail = SCHEDULE_NOT_FOUND
        )

    if current_user.role != "admin":
        employee = (
            db.query(Employee)
            .filter(Employee.user_id == current_user.id)
            .first()
        )

        if not employee:
            raise HTTPException(status_code=403, detail="Not authorized")

        has_access = (
            db.query(Shift)
            .join(Assignment, Assignment.shift_id == Shift.id)
            .filter(
                Shift.schedule_id == schedule_id,
                Assignment.employee_id == employee.id,
            )
            .first()
        )

        if not has_access:
            raise HTTPException(status_code=403, detail="Not authorized")

    shifts = (
        db.query(Shift)
        .filter(Shift.schedule_id == schedule.id)
        .order_by(Shift.start_datetime.asc())
        .all()
    )

    shift_ids = [shift.id for shift in shifts]

    assignments = []
    if shift_ids:
        assignments = (
            db.query(Assignment)
            .filter(Assignment.shift_id.in_(shift_ids))
            .all()
        )

    employee_ids = list({assignment.employee_id for assignment in assignments})

    employees = []
    if employee_ids:
        employees = (
            db.query(Employee)
            .filter(Employee.id.in_(employee_ids))
            .all()
        )

    employees_by_id = {employee.id: employee for employee in employees}
    assignments_by_shift_id: dict[int, list[Assignment]] = {}

    for assignment in assignments:
        assignments_by_shift_id.setdefault(assignment.shift_id, []).append(assignment)

    return {
        "id": schedule.id,
        "start_date": schedule.start_date,
        "end_date": schedule.end_date,
        "status": schedule.status,
        "shifts": [
            {
                "id": shift.id,
                "date": shift.start_datetime.date(),
                "start_time": shift.start_datetime.time(),
                "end_time": shift.end_datetime.time(),
                "status": shift.status,
                "assignments": [
                    {
                        "id": assignment.id,
                        "employee": {
                            "id": employees_by_id[assignment.employee_id].id,
                            "first_name": employees_by_id[assignment.employee_id].first_name,
                            "last_name": employees_by_id[assignment.employee_id].last_name,
                        },
                    }
                    for assignment in assignments_by_shift_id.get(shift.id, [])
                    if assignment.employee_id in employees_by_id
                ],
            }
            for shift in shifts
        ],
    }


@router.put("/{schedule_id}", response_model = ScheduleResponse)
def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_user)]
):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = SCHEDULE_NOT_FOUND
        )

    update_data = schedule_data.model_dump(exclude_unset = True)

    for field, value in update_data.items():
        setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)

    return schedule


@router.delete("/{schedule_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_user)]
):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = SCHEDULE_NOT_FOUND
        )

    db.delete(schedule)
    db.commit()