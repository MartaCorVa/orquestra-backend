from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.shift import Shift
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentResponse

router = APIRouter(prefix = "/assignments", tags = ["Assignments"])


@router.post("/", response_model = AssignmentResponse, status_code = status.HTTP_201_CREATED)
def create_assignment(
    assignment: AssignmentCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_user)]
):
    employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
    shift = db.query(Shift).filter(Shift.id == assignment.shift_id).first()

    if not employee:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Employee does not exist"
        )

    if not shift:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Shift does not exist"
        )

    new_assignment = Assignment(
        employee_id = assignment.employee_id,
        shift_id = assignment.shift_id
    )

    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    return new_assignment


@router.get("/", response_model = list[AssignmentResponse])
def get_assignments(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_user)]
):
    return db.query(Assignment).all()


@router.delete("/{assignment_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin_user)]
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()

    if not assignment:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Assignment not found"
        )

    db.delete(assignment)
    db.commit()