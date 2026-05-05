from uuid import uuid4


def build_user_payload(email = None):
    return {
        "email": email or f"user-{uuid4()}@example.com",
        "password": "password123",
        "role": "employee",
        "active": True,
    }


def test_create_user_requires_admin(client, employee_auth_headers):
    response = client.post(
        "/users/",
        json = build_user_payload(),
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_create_user_success(client, auth_headers):
    payload = build_user_payload()

    response = client.post(
        "/users/",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == payload["email"]
    assert data["role"] == "employee"
    assert data["active"] is True


def test_create_user_returns_400_when_email_exists(client, auth_headers):
    payload = build_user_payload(email = "duplicated@example.com")

    client.post("/users/", json = payload, headers = auth_headers)

    response = client.post(
        "/users/",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already registered"


def test_get_users_requires_admin(client, employee_auth_headers):
    response = client.get(
        "/users/",
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_get_users_success(client, auth_headers):
    response = client.get(
        "/users/",
        headers = auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_user_success(client, auth_headers):
    create = client.post(
        "/users/",
        json = build_user_payload(),
        headers = auth_headers,
    )

    user_id = create.json()["id"]

    response = client.get(
        f"/users/{user_id}",
        headers = auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == user_id


def test_get_user_returns_404(client, auth_headers):
    response = client.get(
        "/users/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_update_user_requires_admin(client, employee_auth_headers, auth_headers):
    create = client.post(
        "/users/",
        json = build_user_payload(),
        headers = auth_headers,
    )

    user_id = create.json()["id"]

    response = client.put(
        f"/users/{user_id}",
        json = {"email": "new@example.com"},
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_update_user_success(client, auth_headers):
    create = client.post(
        "/users/",
        json = build_user_payload(),
        headers = auth_headers,
    )

    user_id = create.json()["id"]

    response = client.put(
        f"/users/{user_id}",
        json = {"email": "updated@example.com"},
        headers = auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["email"] == "updated@example.com"


def test_update_user_returns_404(client, auth_headers):
    response = client.put(
        "/users/9999",
        json = {"email": "updated@example.com"},
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_delete_user_requires_admin(client, employee_auth_headers, auth_headers):
    create = client.post(
        "/users/",
        json = build_user_payload(),
        headers = auth_headers,
    )

    user_id = create.json()["id"]

    response = client.delete(
        f"/users/{user_id}",
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_delete_user_success(client, auth_headers):
    create = client.post(
        "/users/",
        json = build_user_payload(),
        headers = auth_headers,
    )

    user_id = create.json()["id"]

    response = client.delete(
        f"/users/{user_id}",
        headers = auth_headers,
    )

    assert response.status_code == 204


def test_delete_user_returns_404(client, auth_headers):
    response = client.delete(
        "/users/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"