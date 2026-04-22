from datetime import date, datetime

import pytest

from app.core.security import hash_password
from app.models.assignment import Assignment
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.user import User


@pytest.fixture
def metrics_admin_user(db):
    user = User(
        email = "metrics-admin@example.com",
        password = hash_password("testpassword"),
        role = "admin",
        active = True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def metrics_employee_user(db):
    user = User(
        email = "metrics-employee@example.com",
        password = hash_password("testpassword"),
        role = "employee",
        active = True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def metrics_admin_headers(client, metrics_admin_user):
    response = client.post(
        "/auth/login",
        data = {
            "username": "metrics-admin@example.com",
            "password": "testpassword",
        },
    )

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def metrics_employee_headers(client, metrics_employee_user):
    response = client.post(
        "/auth/login",
        data = {
            "username": "metrics-employee@example.com",
            "password": "testpassword",
        },
    )

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def metrics_data(db, metrics_employee_user):
    employee_1 = Employee(
        first_name = "Marta",
        last_name = "Lopez",
        phone_number = "111111111",
        active = True,
        user_id = metrics_employee_user.id,
    )

    employee_2 = Employee(
        first_name = "Juan",
        last_name = "Perez",
        phone_number = "222222222",
        active = True,
        user_id = None,
    )

    schedule = Schedule(
        start_date = date(2026, 3, 1),
        end_date = date(2026, 3, 7),
        status = "published",
    )

    db.add_all([employee_1, employee_2, schedule])
    db.commit()

    db.refresh(employee_1)
    db.refresh(employee_2)
    db.refresh(schedule)

    contract_1 = Contract(
        employee_id = employee_1.id,
        weekly_hours = 40,
        daily_hours = 8,
        min_days_off_per_week = 2,
        work_monday = True,
        work_tuesday = True,
        work_wednesday = True,
        work_thursday = True,
        work_friday = True,
        work_saturday = False,
        work_sunday = False,
        has_fixed_schedule = False,
        preferred_start_time = None,
        preferred_end_time = None,
        active = True,
        start_date = date(2026, 1, 1),
        end_date = None,
    )

    contract_2 = Contract(
        employee_id = employee_2.id,
        weekly_hours = 20,
        daily_hours = 4,
        min_days_off_per_week = 2,
        work_monday = True,
        work_tuesday = True,
        work_wednesday = True,
        work_thursday = True,
        work_friday = True,
        work_saturday = False,
        work_sunday = False,
        has_fixed_schedule = False,
        preferred_start_time = None,
        preferred_end_time = None,
        active = True,
        start_date = date(2026, 1, 1),
        end_date = None,
    )

    db.add_all([contract_1, contract_2])
    db.commit()

    shift_1 = Shift(
        start_datetime = datetime(2026, 3, 2, 9, 0),
        end_datetime = datetime(2026, 3, 2, 13, 0),
        creation_type = "manual",
        status = "assigned",
        schedule_id = schedule.id,
    )

    shift_2 = Shift(
        start_datetime = datetime(2026, 3, 3, 10, 0),
        end_datetime = datetime(2026, 3, 3, 14, 0),
        creation_type = "manual",
        status = "assigned",
        schedule_id = schedule.id,
    )

    db.add_all([shift_1, shift_2])
    db.commit()

    db.refresh(shift_1)
    db.refresh(shift_2)

    assignments = [
        Assignment(employee_id = employee_1.id, shift_id = shift_1.id),
        Assignment(employee_id = employee_2.id, shift_id = shift_2.id),
    ]

    db.add_all(assignments)
    db.commit()

    return {
        "schedule": schedule,
        "employee_1": employee_1,
        "employee_2": employee_2,
        "contract_1": contract_1,
        "contract_2": contract_2,
        "shift_1": shift_1,
        "shift_2": shift_2,
    }


@pytest.fixture
def empty_schedule(db):
    schedule = Schedule(
        start_date = date(2026, 4, 1),
        end_date = date(2026, 4, 7),
        status = "draft",
    )

    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return schedule


@pytest.fixture
def metrics_data_with_contract_change(db, metrics_employee_user):
    employee = Employee(
        first_name = "Laura",
        last_name = "Sanchez",
        phone_number = "333333333",
        active = True,
        user_id = metrics_employee_user.id,
    )

    schedule = Schedule(
        start_date = date(2026, 3, 1),
        end_date = date(2026, 3, 7),
        status = "published",
    )

    db.add_all([employee, schedule])
    db.commit()

    db.refresh(employee)
    db.refresh(schedule)

    old_contract = Contract(
        employee_id = employee.id,
        weekly_hours = 20,
        daily_hours = 4,
        min_days_off_per_week = 2,
        work_monday = True,
        work_tuesday = True,
        work_wednesday = True,
        work_thursday = True,
        work_friday = True,
        work_saturday = False,
        work_sunday = False,
        has_fixed_schedule = False,
        preferred_start_time = None,
        preferred_end_time = None,
        active = False,
        start_date = date(2026, 1, 1),
        end_date = date(2026, 3, 31),
    )

    current_contract = Contract(
        employee_id = employee.id,
        weekly_hours = 40,
        daily_hours = 8,
        min_days_off_per_week = 2,
        work_monday = True,
        work_tuesday = True,
        work_wednesday = True,
        work_thursday = True,
        work_friday = True,
        work_saturday = False,
        work_sunday = False,
        has_fixed_schedule = False,
        preferred_start_time = None,
        preferred_end_time = None,
        active = True,
        start_date = date(2026, 4, 1),
        end_date = None,
    )

    db.add_all([old_contract, current_contract])
    db.commit()

    shift = Shift(
        start_datetime = datetime(2026, 3, 2, 9, 0),
        end_datetime = datetime(2026, 3, 2, 13, 0),
        creation_type = "manual",
        status = "assigned",
        schedule_id = schedule.id,
    )

    db.add(shift)
    db.commit()
    db.refresh(shift)

    assignment = Assignment(employee_id = employee.id, shift_id = shift.id)

    db.add(assignment)
    db.commit()

    return {
        "schedule": schedule,
        "employee": employee,
        "old_contract": old_contract,
        "current_contract": current_contract,
        "shift": shift,
    }