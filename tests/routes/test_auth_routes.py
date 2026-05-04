def test_login_success(client, test_user):
    response = client.post(
        "/auth/login",
        data = {
            "username": "test@example.com",
            "password": "testpassword",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert "access_token" in response_data
    assert "token_type" in response_data
    assert "must_change_password" in response_data
    assert response_data["must_change_password"] is False
    assert response_data["token_type"] == "bearer"


def test_login_fails_with_wrong_password(client, test_user):
    response = client.post(
        "/auth/login",
        data = {
            "username": "test@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_fails_with_unknown_user(client):
    response = client.post(
        "/auth/login",
        data = {
            "username": "unknown@example.com",
            "password": "testpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"