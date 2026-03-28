from datetime import date, time

import pytest

from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.user import User
from app.core.security import hash_password


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
        max_weekly_hours = 40,
        active = True,
        user_id = metrics_employee_user.id,
    )

    employee_2 = Employee(
        first_name = "Juan",
        last_name = "Perez",
        phone_number = "222222222",
        max_weekly_hours = 20,
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

    shift_1 = Shift(
        date = date(2026, 3, 2),
        start_time = time(9, 0),
        end_time = time(13, 0),
        creation_type = "manual",
        status = "assigned",
        schedule_id = schedule.id,
    )

    shift_2 = Shift(
        date = date(2026, 3, 3),
        start_time = time(10, 0),
        end_time = time(14, 0),
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