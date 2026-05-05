def test_create_assignment_requires_admin(client, employee_auth_headers, active_employees, test_shifts):
    payload = {
        "employee_id": active_employees[0].id,
        "shift_id": test_shifts[0].id,
    }

    response = client.post(
        "/assignments/",
        json = payload,
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_create_assignment_success(client, auth_headers, active_employees, test_shifts):
    payload = {
        "employee_id": active_employees[0].id,
        "shift_id": test_shifts[0].id,
    }

    response = client.post(
        "/assignments/",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["employee_id"] == payload["employee_id"]
    assert data["shift_id"] == payload["shift_id"]


def test_create_assignment_returns_400_when_employee_does_not_exist(client, auth_headers, test_shifts):
    payload = {
        "employee_id": 9999,
        "shift_id": test_shifts[0].id,
    }

    response = client.post(
        "/assignments/",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Employee does not exist"


def test_create_assignment_returns_400_when_shift_does_not_exist(client, auth_headers, active_employees):
    payload = {
        "employee_id": active_employees[0].id,
        "shift_id": 9999,
    }

    response = client.post(
        "/assignments/",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Shift does not exist"


def test_get_assignments_requires_admin(client, employee_auth_headers):
    response = client.get(
        "/assignments/",
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_get_assignments_success(client, auth_headers, active_employees, test_shifts):
    client.post(
        "/assignments/",
        json = {
            "employee_id": active_employees[0].id,
            "shift_id": test_shifts[0].id,
        },
        headers = auth_headers,
    )

    response = client.get(
        "/assignments/",
        headers = auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_delete_assignment_requires_admin(client, employee_auth_headers, auth_headers, db, active_employees, test_shifts):
    create = client.post(
        "/assignments/",
        json = {
            "employee_id": active_employees[0].id,
            "shift_id": test_shifts[0].id,
        },
        headers = auth_headers,
    )

    assignment_id = create.json()["id"]

    response = client.delete(
        f"/assignments/{assignment_id}",
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_delete_assignment_success(client, auth_headers, active_employees, test_shifts):
    create = client.post(
        "/assignments/",
        json = {
            "employee_id": active_employees[0].id,
            "shift_id": test_shifts[0].id,
        },
        headers = auth_headers,
    )

    assignment_id = create.json()["id"]

    response = client.delete(
        f"/assignments/{assignment_id}",
        headers = auth_headers,
    )

    assert response.status_code == 204


def test_delete_assignment_returns_404(client, auth_headers):
    response = client.delete(
        "/assignments/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Assignment not found"