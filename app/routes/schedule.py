from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleResponse, ScheduleUpdate

router = APIRouter(prefix = "/schedules", tags = ["Schedules"])


@router.post("/", response_model = ScheduleResponse, status_code = status.HTTP_201_CREATED)
def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    new_schedule = Schedule(
        start_date = schedule.start_date,
        end_date = schedule.end_date,
        status = schedule.status
    )

    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)

    return new_schedule


@router.get("/", response_model = list[ScheduleResponse])
def get_schedules(db: Session = Depends(get_db)):
    return db.query(Schedule).all()


@router.get("/{schedule_id}", response_model = ScheduleResponse)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Schedule not found"
        )

    return schedule


@router.put("/{schedule_id}", response_model = ScheduleResponse)
def update_schedule(schedule_id: int, schedule_data: ScheduleUpdate, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Schedule not found"
        )

    update_data = schedule_data.model_dump(exclude_unset = True)

    for field, value in update_data.items():
        setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)

    return schedule


@router.delete("/{schedule_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Schedule not found"
        )

    db.delete(schedule)
    db.commit()