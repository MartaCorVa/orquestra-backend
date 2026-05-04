def test_create_schedule_requires_admin(client, employee_auth_headers):
    payload = {
        "start_date": "2026-04-01",
        "end_date": "2026-04-07",
        "status": "draft",
    }

    response = client.post(
        "/schedules/",
        json = payload,
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_create_schedule_success(client, auth_headers):
    payload = {
        "start_date": "2026-04-01",
        "end_date": "2026-04-07",
        "status": "draft",
    }

    response = client.post(
        "/schedules/",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["start_date"] == "2026-04-01"
    assert data["end_date"] == "2026-04-07"
    assert data["status"] == "draft"


def test_get_schedules_returns_list_for_admin(client, auth_headers, test_schedule):
    response = client.get(
        "/schedules/",
        headers = auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_schedule_by_id_returns_schedule_detail(client, auth_headers, test_schedule, test_shifts):
    response = client.get(
        f"/schedules/{test_schedule.id}",
        headers = auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == test_schedule.id
    assert data["start_date"] == "2026-03-01"
    assert data["end_date"] == "2026-03-07"
    assert data["status"] == "draft"
    assert len(data["shifts"]) == len(test_shifts)


def test_get_schedule_by_id_returns_404_when_schedule_does_not_exist(client, auth_headers):
    response = client.get(
        "/schedules/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule not found"


def test_update_schedule_requires_admin(client, employee_auth_headers, test_schedule):
    payload = {
        "status": "published",
    }

    response = client.put(
        f"/schedules/{test_schedule.id}",
        json = payload,
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_update_schedule_success(client, auth_headers, test_schedule):
    payload = {
        "status": "published",
    }

    response = client.put(
        f"/schedules/{test_schedule.id}",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == test_schedule.id
    assert data["status"] == "published"


def test_update_schedule_returns_404_when_schedule_does_not_exist(client, auth_headers):
    payload = {
        "status": "published",
    }

    response = client.put(
        "/schedules/9999",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule not found"


def test_delete_schedule_requires_admin(client, employee_auth_headers, test_schedule):
    response = client.delete(
        f"/schedules/{test_schedule.id}",
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_delete_schedule_success(client, auth_headers, test_schedule):
    response = client.delete(
        f"/schedules/{test_schedule.id}",
        headers = auth_headers,
    )

    assert response.status_code == 204


def test_delete_schedule_returns_404_when_schedule_does_not_exist(client, auth_headers):
    response = client.delete(
        "/schedules/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule not found"