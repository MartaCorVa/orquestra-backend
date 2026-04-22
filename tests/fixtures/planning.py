from datetime import date, datetime

import pytest

from app.models.contract import Contract
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
            active = True,
            user_id = None,
        ),
        Employee(
            first_name = "Juan",
            last_name = "Perez",
            phone_number = "222222222",
            active = True,
            user_id = None,
        ),
        Employee(
            first_name = "Ana",
            last_name = "Garcia",
            phone_number = "333333333",
            active = True,
            user_id = None,
        ),
    ]

    db.add_all(employees)
    db.commit()

    for employee in employees:
        db.refresh(employee)

    contracts = [
        Contract(
            employee_id = employees[0].id,
            weekly_hours = 40,
            daily_hours = 12,
            min_days_off_per_week = 0,
            work_monday = True,
            work_tuesday = True,
            work_wednesday = True,
            work_thursday = True,
            work_friday = True,
            work_saturday = True,
            work_sunday = True,
            has_fixed_schedule = False,
            preferred_start_time = None,
            preferred_end_time = None,
            active = True,
            start_date = date(2026, 1, 1),
            end_date = None,
        ),
        Contract(
            employee_id = employees[1].id,
            weekly_hours = 40,
            daily_hours = 12,
            min_days_off_per_week = 0,
            work_monday = True,
            work_tuesday = True,
            work_wednesday = True,
            work_thursday = True,
            work_friday = True,
            work_saturday = True,
            work_sunday = True,
            has_fixed_schedule = False,
            preferred_start_time = None,
            preferred_end_time = None,
            active = True,
            start_date = date(2026, 1, 1),
            end_date = None,
        ),
        Contract(
            employee_id = employees[2].id,
            weekly_hours = 40,
            daily_hours = 12,
            min_days_off_per_week = 0,
            work_monday = True,
            work_tuesday = True,
            work_wednesday = True,
            work_thursday = True,
            work_friday = True,
            work_saturday = True,
            work_sunday = True,
            has_fixed_schedule = False,
            preferred_start_time = None,
            preferred_end_time = None,
            active = True,
            start_date = date(2026, 1, 1),
            end_date = None,
        ),
    ]

    db.add_all(contracts)
    db.commit()

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