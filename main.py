from fastapi import FastAPI

from app.core.database import Base, engine
from app.models import User, Employee, Schedule, Shift, Assignment

app = FastAPI(title="Orquestra API")

Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"message": "Orquestra backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}