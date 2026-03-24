from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate

router = APIRouter(prefix = "/employees", tags = ["Employees"])


@router.post("/", response_model = EmployeeResponse, status_code = status.HTTP_201_CREATED)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    if employee.user_id is not None:
        user = db.query(User).filter(User.id == employee.user_id).first()
        if not user:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Assigned user does not exist"
            )

    new_employee = Employee(
        first_name = employee.first_name,
        last_name = employee.last_name,
        phone_number = employee.phone_number,
        max_weekly_hours = employee.max_weekly_hours,
        active = employee.active,
        user_id = employee.user_id
    )

    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    return new_employee


@router.get("/", response_model = list[EmployeeResponse])
def get_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()


@router.get("/{employee_id}", response_model = EmployeeResponse)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Employee not found"
        )

    return employee


@router.put("/{employee_id}", response_model = EmployeeResponse)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Employee not found"
        )

    if employee_data.user_id is not None:
        user = db.query(User).filter(User.id == employee_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Assigned user does not exist"
            )

    update_data = employee_data.model_dump(exclude_unset = True)

    for field, value in update_data.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)

    return employee


@router.delete("/{employee_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Employee not found"
        )

    db.delete(employee)
    db.commit()