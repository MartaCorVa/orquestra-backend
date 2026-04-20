from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from app.schemas.employee_onboarding import EmployeeOnboardingCreate, EmployeeOnboardingResponse
from app.services.employee_onboarding_service import create_employee_with_user

router = APIRouter(prefix = "/employees", tags = ["Employees"])


@router.post("/", response_model = EmployeeResponse, status_code = status.HTTP_201_CREATED)
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
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
        active = employee.active,
        user_id = employee.user_id
    )

    db.add(new_employee)
    db.flush()

    new_contract = Contract(
        employee_id = new_employee.id,
        weekly_hours = employee.contract.weekly_hours,
        daily_hours = employee.contract.daily_hours,
        min_days_off_per_week = employee.contract.min_days_off_per_week,
        work_monday = employee.contract.work_monday,
        work_tuesday = employee.contract.work_tuesday,
        work_wednesday = employee.contract.work_wednesday,
        work_thursday = employee.contract.work_thursday,
        work_friday = employee.contract.work_friday,
        work_saturday = employee.contract.work_saturday,
        work_sunday = employee.contract.work_sunday,
        has_fixed_schedule = employee.contract.has_fixed_schedule,
        preferred_start_time = employee.contract.preferred_start_time,
        preferred_end_time = employee.contract.preferred_end_time,
        active = employee.contract.active,
        start_date = employee.contract.start_date,
        end_date = employee.contract.end_date,
    )

    db.add(new_contract)
    db.commit()
    db.refresh(new_employee)

    return (
        db.query(Employee)
        .options(joinedload(Employee.contract))
        .filter(Employee.id == new_employee.id)
        .first()
    )


@router.post("/onboarding", response_model = EmployeeOnboardingResponse, status_code = status.HTTP_201_CREATED)
def onboard_employee(
    payload: EmployeeOnboardingCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    try:
        result = create_employee_with_user(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = str(exc)
        )

    return {
        "user_id": result["user"].id,
        "employee_id": result["employee"].id,
        "email": result["user"].email,
        "role": result["user"].role,
        "must_change_password": result["user"].must_change_password,
        "first_name": result["employee"].first_name,
        "last_name": result["employee"].last_name,
        "phone_number": result["employee"].phone_number,
        "active": result["employee"].active
    }


@router.get("/", response_model = list[EmployeeResponse])
def get_employees(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    return db.query(Employee).options(joinedload(Employee.contract)).all()


@router.get("/{employee_id}", response_model = EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
):
    employee = (
        db.query(Employee)
        .options(joinedload(Employee.contract))
        .filter(Employee.id == employee_id)
        .first()
    )

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
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    employee = (
        db.query(Employee)
        .options(joinedload(Employee.contract))
        .filter(Employee.id == employee_id)
        .first()
    )

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

    contract_data = update_data.pop("contract", None)

    for field, value in update_data.items():
        setattr(employee, field, value)

    if contract_data is not None:
        if employee.contract is None:
            if "weekly_hours" not in contract_data or "daily_hours" not in contract_data:
                raise HTTPException(
                    status_code = status.HTTP_400_BAD_REQUEST,
                    detail = "weekly_hours and daily_hours are required to create a contract"
                )

            employee.contract = Contract(
                employee_id = employee.id,
                weekly_hours = contract_data["weekly_hours"],
                daily_hours = contract_data["daily_hours"],
                min_days_off_per_week = contract_data.get("min_days_off_per_week", 2),
                work_monday = contract_data.get("work_monday", True),
                work_tuesday = contract_data.get("work_tuesday", True),
                work_wednesday = contract_data.get("work_wednesday", True),
                work_thursday = contract_data.get("work_thursday", True),
                work_friday = contract_data.get("work_friday", True),
                work_saturday = contract_data.get("work_saturday", False),
                work_sunday = contract_data.get("work_sunday", False),
                has_fixed_schedule = contract_data.get("has_fixed_schedule", False),
                preferred_start_time = contract_data.get("preferred_start_time"),
                preferred_end_time = contract_data.get("preferred_end_time"),
                active = contract_data.get("active", True),
                start_date = contract_data.get("start_date"),
                end_date = contract_data.get("end_date"),
            )
        else:
            for field, value in contract_data.items():
                setattr(employee.contract, field, value)

    db.commit()
    db.refresh(employee)

    return (
        db.query(Employee)
        .options(joinedload(Employee.contract))
        .filter(Employee.id == employee.id)
        .first()
    )


@router.delete("/{employee_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Employee not found"
        )

    db.delete(employee)
    db.commit()