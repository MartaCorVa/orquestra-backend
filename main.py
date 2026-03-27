from fastapi import FastAPI

from app.core.database import Base, engine
from app.models import Assignment, Employee, Schedule, Shift, User
from app.routes.assignment import router as assignment_router
from app.routes.employee import router as employee_router
from app.routes.schedule import router as schedule_router
from app.routes.shift import router as shift_router
from app.routes.user import router as user_router
from app.routes.auth import router as auth_router
from app.routes.planning import router as planning_router
from app.routes.metrics import router as metrics_router

app = FastAPI(title = "Orquestra API")

@app.get("/")
def read_root():
    return {"message": "Orquestra backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(employee_router)
app.include_router(schedule_router)
app.include_router(shift_router)
app.include_router(assignment_router)
app.include_router(planning_router)
app.include_router(metrics_router)