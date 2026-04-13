from datetime import date, datetime

import pytest

from app.models.employee import Employee
from app.models.schedule import Schedule
from app.models.shift import Shift


@pytest.fixture
def test_schedule(db):
    schedule = Schedule(
        start_date = date(2026, 3, 1),
        end_date = date(2026, 3, 7),
        status = "draft",
    )

    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return schedule


@pytest.fixture
def active_employees(db):
    employees = [
        Employee(
            first_name = "Marta",
            last_name = "Lopez",
            phone_number = "111111111",
            max_weekly_hours = 40,
            active = True,
            user_id = None,
        ),
        Employee(
            first_name = "Juan",
            last_name = "Perez",
            phone_number = "222222222",
            max_weekly_hours = 40,
            active = True,
            user_id = None,
        ),
        Employee(
            first_name = "Ana",
            last_name = "Garcia",
            phone_number = "333333333",
            max_weekly_hours = 40,
            active = True,
            user_id = None,
        ),
    ]

    db.add_all(employees)
    db.commit()

    for employee in employees:
        db.refresh(employee)

    return employees


@pytest.fixture
def test_shifts(db, test_schedule):
    shifts = [
        Shift(
            start_datetime = datetime(2026, 3, 1, 9, 0),
            end_datetime = datetime(2026, 3, 1, 13, 0),
            creation_type = "manual",
            status = "pending",
            schedule_id = test_schedule.id,
        ),
        Shift(
            start_datetime = datetime(2026, 3, 1, 14, 0),
            end_datetime = datetime(2026, 3, 1, 18, 0),
            creation_type = "manual",
            status = "pending",
            schedule_id = test_schedule.id,
        ),
    ]

    db.add_all(shifts)
    db.commit()

    for shift in shifts:
        db.refresh(shift)

    return shifts