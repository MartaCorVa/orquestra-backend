from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.schedule import Schedule
from app.models.user import User
from app.services.planning_service import generate_schedule

router = APIRouter(prefix = "/planning", tags = ["Planning"])


@router.post("/generate/{schedule_id}", status_code = status.HTTP_200_OK)
def generate_planning(
    schedule_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_user)]
):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Schedule not found",
        )

    return generate_schedule(
        db = db,
        schedule_id = schedule_id
    )