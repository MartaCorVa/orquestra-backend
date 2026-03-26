from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.schedule import Schedule
from app.models.user import User
from app.schemas.planning import PlanningGenerateRequest
from app.services.planning_service import generate_schedule

router = APIRouter(prefix = "/planning", tags = ["Planning"])

@router.post("/generate/{schedule_id}")
def generate(
    schedule_id: int,
    payload: PlanningGenerateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(status_code = 404, detail = "Schedule not found")
    
    result = generate_schedule(
        db,
        schedule_id,
        employees_per_shift = payload.employees_per_shift
    )

    return {"assignments_created": len(result)}