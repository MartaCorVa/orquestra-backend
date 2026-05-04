from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.services.shift_service import (
    normalize_datetime,
    validate_schedule_exists,
    validate_employee_for_assignment,
    validate_shift_creation,
)


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeDB:
    def __init__(self, result = None):
        self.result = result

    def query(self, model):
        return FakeQuery(self.result)


class FakeContract:
    def __init__(self, active = True):
        self.active = active


class FakeEmployee:
    def __init__(self, active = True, contracts = None, id = 1):
        self.id = id
        self.active = active
        self.contracts = contracts or []


class FakeSchedule:
    id = 1


def test_normalize_datetime_converts_timezone_aware_to_naive_utc():
    aware_datetime = datetime(2025, 1, 1, 10, 0, tzinfo = timezone.utc)

    result = normalize_datetime(aware_datetime)

    assert result.tzinfo is None
    assert result == datetime(2025, 1, 1, 10, 0)


def test_normalize_datetime_keeps_naive_datetime():
    naive_datetime = datetime(2025, 1, 1, 10, 0)

    result = normalize_datetime(naive_datetime)

    assert result == naive_datetime


def test_validate_schedule_exists_returns_schedule():
    schedule = FakeSchedule()
    db = FakeDB(result = schedule)

    result = validate_schedule_exists(db = db, schedule_id = 1)

    assert result == schedule


def test_validate_schedule_exists_raises_when_schedule_does_not_exist():
    db = FakeDB(result = None)

    with pytest.raises(HTTPException) as exc:
        validate_schedule_exists(db = db, schedule_id = 999)

    assert exc.value.status_code == 400
    assert "Schedule does not exist" in exc.value.detail["errors"]


def test_validate_employee_for_assignment_returns_active_employee():
    employee = FakeEmployee(active = True)
    db = FakeDB(result = employee)

    result = validate_employee_for_assignment(db = db, employee_id = 1)

    assert result == employee


def test_validate_employee_for_assignment_raises_when_employee_does_not_exist():
    db = FakeDB(result = None)

    with pytest.raises(HTTPException) as exc:
        validate_employee_for_assignment(db = db, employee_id = 999)

    assert exc.value.status_code == 400
    assert "Employee does not exist" in exc.value.detail["errors"]


def test_validate_employee_for_assignment_raises_when_employee_is_inactive():
    employee = FakeEmployee(active = False)
    db = FakeDB(result = employee)

    with pytest.raises(HTTPException) as exc:
        validate_employee_for_assignment(db = db, employee_id = 1)

    assert exc.value.status_code == 400
    assert "Employee is not active" in exc.value.detail["errors"]


def test_validate_shift_creation_raises_when_end_datetime_is_before_start(monkeypatch):
    monkeypatch.setattr(
        "app.services.shift_service.validate_shift_within_schedule",
        lambda **kwargs: [],
    )

    db = FakeDB()
    schedule = FakeSchedule()

    with pytest.raises(HTTPException) as exc:
        validate_shift_creation(
            db = db,
            start_datetime = datetime(2025, 1, 1, 12, 0),
            end_datetime = datetime(2025, 1, 1, 10, 0),
            schedule = schedule,
        )

    assert exc.value.status_code == 400
    assert "End datetime must be later than start datetime" in exc.value.detail["errors"]


def test_validate_shift_creation_raises_when_employee_has_no_active_contract(monkeypatch):
    monkeypatch.setattr(
        "app.services.shift_service.validate_shift_within_schedule",
        lambda **kwargs: [],
    )

    db = FakeDB()
    schedule = FakeSchedule()
    employee = FakeEmployee(active = True, contracts = [FakeContract(active = False)])

    with pytest.raises(HTTPException) as exc:
        validate_shift_creation(
            db = db,
            start_datetime = datetime(2025, 1, 1, 10, 0),
            end_datetime = datetime(2025, 1, 1, 12, 0),
            schedule = schedule,
            employee = employee,
        )

    assert exc.value.status_code == 400
    assert "Employee does not have an active contract" in exc.value.detail["errors"]


def test_validate_shift_creation_passes_with_valid_data_without_employee(monkeypatch):
    monkeypatch.setattr(
        "app.services.shift_service.validate_shift_within_schedule",
        lambda **kwargs: [],
    )

    db = FakeDB()
    schedule = FakeSchedule()

    validate_shift_creation(
        db = db,
        start_datetime = datetime(2025, 1, 1, 10, 0),
        end_datetime = datetime(2025, 1, 1, 12, 0),
        schedule = schedule,
        employee = None,
    )