from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.schemas.planning import GeneratePlanningRequest
from app.services.planning_service import generate_schedule

router = APIRouter(prefix = "/planning", tags = ["Planning"])


@router.post("/generate", status_code = status.HTTP_200_OK)
def generate_planning(
    payload: GeneratePlanningRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    return generate_schedule(
        db = db,
        schedule_id = payload.schedule_id,
        employees_per_shift = payload.employees_per_shift
    )