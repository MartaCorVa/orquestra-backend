from sqlalchemy.orm import Session

from app.core.security import hash_password
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
            max_weekly_hours = payload.max_weekly_hours,
            active = payload.active,
            user_id = new_user.id
        )

        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)
        db.refresh(new_user)

        return {
            "user": new_user,
            "employee": new_employee
        }

    except Exception:
        db.rollback()
        raise