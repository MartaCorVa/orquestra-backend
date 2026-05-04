from datetime import datetime


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