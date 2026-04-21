from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.user import User
from app.schemas.contract import ContractCreate, ContractResponse, ContractUpdate

router = APIRouter(prefix = "/contracts", tags = ["Contracts"])


@router.post("/", response_model = ContractResponse, status_code = status.HTTP_201_CREATED)
def create_contract(
    contract: ContractCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    employee = db.query(Employee).filter(Employee.id == contract.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Employee does not exist"
        )

    if contract.active:
        (
            db.query(Contract)
            .filter(
                Contract.employee_id == contract.employee_id,
                Contract.active == True
            )
            .update({"active": False})
        )

    new_contract = Contract(
        employee_id = contract.employee_id,
        weekly_hours = contract.weekly_hours,
        daily_hours = contract.daily_hours,
        min_days_off_per_week = contract.min_days_off_per_week,
        work_monday = contract.work_monday,
        work_tuesday = contract.work_tuesday,
        work_wednesday = contract.work_wednesday,
        work_thursday = contract.work_thursday,
        work_friday = contract.work_friday,
        work_saturday = contract.work_saturday,
        work_sunday = contract.work_sunday,
        has_fixed_schedule = contract.has_fixed_schedule,
        preferred_start_time = contract.preferred_start_time,
        preferred_end_time = contract.preferred_end_time,
        active = contract.active,
        start_date = contract.start_date,
        end_date = contract.end_date,
    )

    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)

    return new_contract


@router.get("/employee/{employee_id}", response_model = list[ContractResponse])
def get_employee_contracts(
    employee_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Employee not found"
        )

    return (
        db.query(Contract)
        .filter(Contract.employee_id == employee_id)
        .order_by(Contract.created_at.desc())
        .all()
    )


@router.patch("/{contract_id}/activate", response_model = ContractResponse)
def activate_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Contract not found"
        )

    (
        db.query(Contract)
        .filter(
            Contract.employee_id == contract.employee_id,
            Contract.active == True
        )
        .update({"active": False})
    )

    contract.active = True

    db.commit()
    db.refresh(contract)

    return contract


@router.get("/{contract_id}", response_model = ContractResponse)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Contract not found"
        )

    return contract


@router.put("/{contract_id}", response_model = ContractResponse)
def update_contract(
    contract_id: int,
    contract_data: ContractUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Contract not found"
        )

    update_data = contract_data.model_dump(exclude_unset = True)

    if update_data.get("active") is True:
        (
            db.query(Contract)
            .filter(
                Contract.employee_id == contract.employee_id,
                Contract.id != contract.id,
                Contract.active == True
            )
            .update({"active": False})
        )

    for field, value in update_data.items():
        setattr(contract, field, value)

    db.commit()
    db.refresh(contract)

    return contract


@router.delete("/{contract_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Contract not found"
        )

    db.delete(contract)
    db.commit()