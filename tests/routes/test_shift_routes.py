from datetime import date, datetime, time

from fastapi import HTTPException
import pytest

from app.routes.shift import create_or_update_recurrent_shift_for_date, get_employee_and_contract_for_recurrent_shift, validate_recurrent_shift_payload
from app.schemas.shift import RecurrentShiftCreate


def test_create_shift_requires_admin(client, employee_auth_headers, test_schedule):
    payload = {
        "start_datetime": "2026-03-02T09:00:00",
        "end_datetime": "2026-03-02T13:00:00",
        "creation_type": "manual",
        "status": "pending",
        "schedule_id": test_schedule.id,
        "employee_id": None,
    }

    response = client.post(
        "/shifts/",
        json = payload,
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_create_shift_success(client, auth_headers, test_schedule):
    payload = {
        "start_datetime": "2026-03-02T09:00:00",
        "end_datetime": "2026-03-02T13:00:00",
        "creation_type": "manual",
        "status": "pending",
        "schedule_id": test_schedule.id,
        "employee_id": None,
    }

    response = client.post(
        "/shifts/",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["start_datetime"] == "2026-03-02T09:00:00"
    assert data["end_datetime"] == "2026-03-02T13:00:00"
    assert data["creation_type"] == "manual"
    assert data["status"] == "pending"
    assert data["schedule_id"] == test_schedule.id
    assert data["employee_id"] is None


def test_get_shifts_returns_list_for_admin(client, auth_headers, test_shifts):
    response = client.get(
        "/shifts/",
        headers = auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_get_shifts_table_returns_list_for_admin(client, auth_headers, test_shifts):
    response = client.get(
        "/shifts/table",
        headers = auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_get_shift_returns_shift(client, auth_headers, test_shifts):
    shift = test_shifts[0]

    response = client.get(
        f"/shifts/{shift.id}",
        headers = auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == shift.id
    assert data["status"] == shift.status
    assert data["creation_type"] == shift.creation_type
    assert data["schedule_id"] == shift.schedule_id


def test_get_shift_returns_404_when_shift_does_not_exist(client, auth_headers):
    response = client.get(
        "/shifts/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Shift not found"


def test_update_shift_requires_admin(client, employee_auth_headers, test_shifts):
    shift = test_shifts[0]

    payload = {
        "start_datetime": "2026-03-01T10:00:00",
        "end_datetime": "2026-03-01T14:00:00",
        "creation_type": "manual",
        "status": "confirmed",
        "schedule_id": shift.schedule_id,
        "employee_id": None,
    }

    response = client.put(
        f"/shifts/{shift.id}",
        json = payload,
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_update_shift_success(client, auth_headers, test_shifts):
    shift = test_shifts[0]

    payload = {
        "start_datetime": "2026-03-01T10:00:00",
        "end_datetime": "2026-03-01T14:00:00",
        "creation_type": "manual",
        "status": "confirmed",
        "schedule_id": shift.schedule_id,
        "employee_id": None,
    }

    response = client.put(
        f"/shifts/{shift.id}",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == shift.id
    assert data["start_datetime"] == "2026-03-01T10:00:00"
    assert data["end_datetime"] == "2026-03-01T14:00:00"
    assert data["status"] == "confirmed"


def test_delete_shift_requires_admin(client, employee_auth_headers, test_shifts):
    shift = test_shifts[0]

    response = client.delete(
        f"/shifts/{shift.id}",
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_delete_shift_success(client, auth_headers, test_shifts):
    shift = test_shifts[0]

    response = client.delete(
        f"/shifts/{shift.id}",
        headers = auth_headers,
    )

    assert response.status_code == 204


def test_delete_shift_returns_404_when_shift_does_not_exist(client, auth_headers):
    response = client.delete(
        "/shifts/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Shift not found"


def test_create_shift_returns_400_when_schedule_not_exists(client, auth_headers):
    payload = {
        "start_datetime": "2026-03-01T09:00:00",
        "end_datetime": "2026-03-01T13:00:00",
        "creation_type": "manual",
        "status": "pending",
        "schedule_id": 9999,
        "employee_id": None,
    }

    response = client.post(
        "/shifts/",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 400


def test_get_shifts_returns_empty_when_employee_not_linked(client, employee_auth_headers):
    response = client.get(
        "/shifts/",
        headers = employee_auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_shift_returns_404(client, auth_headers):
    response = client.get(
        "/shifts/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404


def test_update_shift_returns_404(client, auth_headers, test_schedule):
    payload = {
        "start_datetime": "2026-03-01T09:00:00",
        "end_datetime": "2026-03-01T13:00:00",
        "creation_type": "manual",
        "status": "pending",
        "schedule_id": test_schedule.id,
        "employee_id": None,
    }

    response = client.put(
        "/shifts/9999",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Shift not found"


def test_delete_shift_returns_404(client, auth_headers):
    response = client.delete(
        "/shifts/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404


def build_recurrent_payload(**overrides):
    payload = {
        "start_date": date(2026, 3, 2),
        "end_date": date(2026, 3, 6),
        "start_time": time(9, 0),
        "end_time": time(13, 0),
        "weekdays": ["monday", "wednesday"],
        "creation_type": "manual",
        "status": "pending",
        "schedule_id": 1,
        "employee_id": None,
    }

    payload.update(overrides)

    return RecurrentShiftCreate(**payload)


def test_validate_recurrent_shift_payload_returns_selected_weekdays():
    payload = build_recurrent_payload()

    result = validate_recurrent_shift_payload(payload)

    assert result == {0, 2}


def test_get_employee_and_contract_for_recurrent_shift_returns_none_without_employee(db):
    payload = build_recurrent_payload(employee_id = None)

    employee, contract = get_employee_and_contract_for_recurrent_shift(
        db = db,
        payload = payload,
        selected_weekdays = {0, 2},
    )

    assert employee is None
    assert contract is None


def test_get_employee_and_contract_for_recurrent_shift_returns_employee_and_contract(
    db,
    active_employees,
):
    employee = active_employees[0]
    payload = build_recurrent_payload(employee_id = employee.id)

    result_employee, contract = get_employee_and_contract_for_recurrent_shift(
        db = db,
        payload = payload,
        selected_weekdays = {0, 2},
    )

    assert result_employee.id == employee.id
    assert contract.employee_id == employee.id


def test_get_employee_and_contract_for_recurrent_shift_raises_when_employee_missing(db):
    payload = build_recurrent_payload(employee_id = 9999)

    with pytest.raises(HTTPException) as exc:
        get_employee_and_contract_for_recurrent_shift(
            db = db,
            payload = payload,
            selected_weekdays = {0},
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Employee does not exist"


def test_create_or_update_recurrent_shift_for_date_returns_existing_shift(
    db,
    test_schedule,
    test_shifts,
):
    shift = test_shifts[0]
    payload = build_recurrent_payload(
        start_time = shift.start_datetime.time(),
        end_time = shift.end_datetime.time(),
        schedule_id = test_schedule.id,
        employee_id = None,
    )

    result = create_or_update_recurrent_shift_for_date(
        db = db,
        payload = payload,
        current_date = shift.start_datetime.date(),
        employee = None,
        active_contract = None,
    )

    assert result.id == shift.id


def test_create_or_update_recurrent_shift_for_date_creates_new_shift(
    db,
    test_schedule,
):
    payload = build_recurrent_payload(
        start_date = date(2026, 3, 3),
        end_date = date(2026, 3, 3),
        start_time = time(9, 0),
        end_time = time(13, 0),
        schedule_id = test_schedule.id,
        employee_id = None,
    )

    result = create_or_update_recurrent_shift_for_date(
        db = db,
        payload = payload,
        current_date = date(2026, 3, 3),
        employee = None,
        active_contract = None,
    )

    assert result.id is not None
    assert result.schedule_id == test_schedule.id