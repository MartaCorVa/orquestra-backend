from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.schedule import Schedule
from app.models.user import User
from app.schemas.metrics import ScheduleFairnessResponse
from app.services.metrics_service import calculate_schedule_fairness

router = APIRouter(prefix = "/metrics", tags = ["Metrics"])


@router.get("/fairness/{schedule_id}", response_model = ScheduleFairnessResponse)
def get_schedule_fairness(
    schedule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(status_code = 404, detail = "Schedule not found")

    return calculate_schedule_fairness(db, schedule_id)