def build_employee_payload(user_id = None):
    return {
        "first_name": "Test",
        "last_name": "Employee",
        "phone_number": "611111111",
        "active": True,
        "user_id": user_id,
    }


def test_create_employee_requires_admin(client, employee_auth_headers):
    response = client.post(
        "/employees/",
        json = build_employee_payload(),
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_create_employee_success(client, auth_headers):
    payload = build_employee_payload()

    response = client.post(
        "/employees/",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["first_name"] == payload["first_name"]
    assert data["last_name"] == payload["last_name"]
    assert data["phone_number"] == payload["phone_number"]
    assert data["active"] is True


def test_create_employee_returns_400_when_assigned_user_does_not_exist(client, auth_headers):
    payload = build_employee_payload(user_id = 9999)

    response = client.post(
        "/employees/",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Assigned user does not exist"


def test_get_employees_requires_admin(client, employee_auth_headers):
    response = client.get(
        "/employees/",
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_get_employees_success(client, auth_headers, active_employees):
    response = client.get(
        "/employees/",
        headers = auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) >= len(active_employees)


def test_get_employee_success(client, auth_headers, active_employees):
    employee = active_employees[0]

    response = client.get(
        f"/employees/{employee.id}",
        headers = auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == employee.id
    assert data["first_name"] == employee.first_name
    assert data["last_name"] == employee.last_name


def test_get_employee_returns_404(client, auth_headers):
    response = client.get(
        "/employees/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Employee not found"


def test_update_employee_requires_admin(client, employee_auth_headers, active_employees):
    employee = active_employees[0]

    response = client.put(
        f"/employees/{employee.id}",
        json = {"first_name": "Updated"},
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_update_employee_success(client, auth_headers, active_employees):
    employee = active_employees[0]

    response = client.put(
        f"/employees/{employee.id}",
        json = {"first_name": "Updated"},
        headers = auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"


def test_update_employee_returns_400_when_assigned_user_does_not_exist(
    client,
    auth_headers,
    active_employees,
):
    employee = active_employees[0]

    response = client.put(
        f"/employees/{employee.id}",
        json = {"user_id": 9999},
        headers = auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Assigned user does not exist"


def test_update_employee_returns_404(client, auth_headers):
    response = client.put(
        "/employees/9999",
        json = {"first_name": "Updated"},
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Employee not found"


def test_delete_employee_requires_admin(client, employee_auth_headers, active_employees):
    employee = active_employees[0]

    response = client.delete(
        f"/employees/{employee.id}",
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_delete_employee_success(client, auth_headers, active_employees):
    employee = active_employees[0]

    response = client.delete(
        f"/employees/{employee.id}",
        headers = auth_headers,
    )

    assert response.status_code == 204


def test_delete_employee_returns_404(client, auth_headers):
    response = client.delete(
        "/employees/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Employee not found"