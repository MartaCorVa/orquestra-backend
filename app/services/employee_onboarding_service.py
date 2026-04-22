from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee_onboarding import EmployeeOnboardingCreate


def create_employee_with_user(db: Session, payload: EmployeeOnboardingCreate):
    existing_user = db.query(User).filter(User.email == payload.email).first()

    if existing_user:
        raise ValueError("Email is already registered")

    try:
        new_user = User(
            email = payload.email,
            password = hash_password(payload.password),
            role = payload.role,
            active = payload.active,
            must_change_password = True
        )

        db.add(new_user)
        db.flush()

        new_employee = Employee(
            first_name = payload.first_name,
            last_name = payload.last_name,
            phone_number = payload.phone_number,
            active = payload.active,
            user_id = new_user.id
        )

        db.add(new_employee)
        db.flush()

        new_contract = Contract(
            employee_id = new_employee.id,
            weekly_hours = payload.contract.weekly_hours,
            daily_hours = payload.contract.daily_hours,
            min_days_off_per_week = payload.contract.min_days_off_per_week,
            work_monday = payload.contract.work_monday,
            work_tuesday = payload.contract.work_tuesday,
            work_wednesday = payload.contract.work_wednesday,
            work_thursday = payload.contract.work_thursday,
            work_friday = payload.contract.work_friday,
            work_saturday = payload.contract.work_saturday,
            work_sunday = payload.contract.work_sunday,
            has_fixed_schedule = payload.contract.has_fixed_schedule,
            preferred_start_time = payload.contract.preferred_start_time,
            preferred_end_time = payload.contract.preferred_end_time,
            active = payload.contract.active,
            start_date = payload.contract.start_date,
            end_date = payload.contract.end_date,
        )

        db.add(new_contract)
        db.commit()
        db.refresh(new_user)
        db.refresh(new_employee)
        db.refresh(new_contract)

        return {
            "user": new_user,
            "employee": new_employee,
            "contract": new_contract
        }

    except Exception:
        db.rollback()
        raise