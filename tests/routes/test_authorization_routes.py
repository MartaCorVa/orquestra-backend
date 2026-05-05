def test_admin_endpoint_requires_token(client):
    response = client.get("/users/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_admin_endpoint_forbids_non_admin_user(client, employee_auth_headers):
    response = client.get(
        "/users/",
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_admin_endpoint_allows_admin_user(client, auth_headers):
    response = client.get(
        "/users/",
        headers = auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_active_user_endpoint_forbids_inactive_user(client, inactive_auth_headers, inactive_user):
    response = client.get(
        f"/users/{inactive_user.id}",
        headers = inactive_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Inactive user"