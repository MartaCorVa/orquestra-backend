from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.schemas.shift import ShiftUpdate
from app.services.shift_service import (
    apply_shift_update_values,
    get_employee_for_shift_update,
    get_shift_or_raise,
    normalize_datetime,
    update_shift_assignment,
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


class FakeShift:
    def __init__(
        self,
        id = 1,
        start_datetime = None,
        end_datetime = None,
        creation_type = "manual",
        status = "pending",
        schedule_id = 1,
    ):
        self.id = id
        self.start_datetime = start_datetime or datetime(2025, 1, 1, 10, 0)
        self.end_datetime = end_datetime or datetime(2025, 1, 1, 12, 0)
        self.creation_type = creation_type
        self.status = status
        self.schedule_id = schedule_id


class FakeAssignment:
    def __init__(self, employee_id = 1, shift_id = 1):
        self.employee_id = employee_id
        self.shift_id = shift_id


class FakeTrackingDB(FakeDB):
    def __init__(self, result = None):
        super().__init__(result = result)
        self.added = []
        self.deleted = []

    def add(self, item):
        self.added.append(item)

    def delete(self, item):
        self.deleted.append(item)


def test_get_shift_or_raise_returns_shift():
    shift = FakeShift()
    db = FakeDB(result = shift)

    result = get_shift_or_raise(db = db, shift_id = 1)

    assert result == shift


def test_get_shift_or_raise_raises_when_shift_does_not_exist():
    db = FakeDB(result = None)

    with pytest.raises(HTTPException) as exc:
        get_shift_or_raise(db = db, shift_id = 999)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Shift not found"


def test_get_employee_for_shift_update_returns_none_when_employee_id_sent_as_none():
    shift_data = ShiftUpdate(
        start_datetime = datetime(2025, 1, 1, 10, 0),
        end_datetime = datetime(2025, 1, 1, 12, 0),
        employee_id = None,
    )

    result = get_employee_for_shift_update(
        db = FakeDB(),
        shift_data = shift_data,
        current_assignment = FakeAssignment(),
    )

    assert result is None


def test_get_employee_for_shift_update_returns_employee_from_current_assignment():
    employee = FakeEmployee(active = True)
    db = FakeDB(result = employee)

    shift_data = ShiftUpdate(
        start_datetime = datetime(2025, 1, 1, 10, 0),
        end_datetime = datetime(2025, 1, 1, 12, 0),
    )

    result = get_employee_for_shift_update(
        db = db,
        shift_data = shift_data,
        current_assignment = FakeAssignment(employee_id = employee.id),
    )

    assert result == employee


def test_apply_shift_update_values_updates_shift():
    shift = FakeShift()

    update_data = {
        "start_datetime": datetime(2025, 1, 2, 10, 0),
        "end_datetime": datetime(2025, 1, 2, 12, 0),
        "creation_type": "automatic",
        "status": "confirmed",
        "schedule_id": 2,
    }

    apply_shift_update_values(
        shift = shift,
        update_data = update_data,
    )

    assert shift.start_datetime == update_data["start_datetime"]
    assert shift.end_datetime == update_data["end_datetime"]
    assert shift.creation_type == "automatic"
    assert shift.status == "confirmed"
    assert shift.schedule_id == 2


def test_update_shift_assignment_deletes_assignment_when_employee_id_is_none():
    db = FakeTrackingDB()
    current_assignment = FakeAssignment()

    shift_data = ShiftUpdate(
        start_datetime = datetime(2025, 1, 1, 10, 0),
        end_datetime = datetime(2025, 1, 1, 12, 0),
        employee_id = None,
    )

    update_shift_assignment(
        db = db,
        shift = FakeShift(),
        shift_data = shift_data,
        employee = None,
        current_assignment = current_assignment,
    )

    assert db.deleted == [current_assignment]


def test_update_shift_assignment_adds_assignment_when_missing():
    db = FakeTrackingDB()
    employee = FakeEmployee(id = 3)

    shift_data = ShiftUpdate(
        start_datetime = datetime(2025, 1, 1, 10, 0),
        end_datetime = datetime(2025, 1, 1, 12, 0),
        employee_id = employee.id,
    )

    update_shift_assignment(
        db = db,
        shift = FakeShift(id = 5),
        shift_data = shift_data,
        employee = employee,
        current_assignment = None,
    )

    assert len(db.added) == 1
    assert db.added[0].employee_id == employee.id
    assert db.added[0].shift_id == 5


def test_update_shift_assignment_updates_existing_assignment():
    db = FakeTrackingDB()
    employee = FakeEmployee(id = 4)
    current_assignment = FakeAssignment(employee_id = 1)

    shift_data = ShiftUpdate(
        start_datetime = datetime(2025, 1, 1, 10, 0),
        end_datetime = datetime(2025, 1, 1, 12, 0),
        employee_id = employee.id,
    )

    update_shift_assignment(
        db = db,
        shift = FakeShift(),
        shift_data = shift_data,
        employee = employee,
        current_assignment = current_assignment,
    )

    assert current_assignment.employee_id == employee.id