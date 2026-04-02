from app.models.employee import Employee
from app.models.user import User


def test_employee_onboarding_creates_user_and_employee(client, auth_headers, db):
    response = client.post(
        "/employees/onboarding",
        json = {
            "email": "new.employee@example.com",
            "password": "temporary123",
            "role": "employee",
            "first_name": "Laura",
            "last_name": "Martin",
            "phone_number": "600111222",
            "max_weekly_hours": 40,
            "active": True
        },
        headers = auth_headers
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["email"] == "new.employee@example.com"
    assert response_data["role"] == "employee"
    assert response_data["must_change_password"] is True
    assert response_data["first_name"] == "Laura"
    assert response_data["last_name"] == "Martin"
    assert response_data["max_weekly_hours"] == 40
    assert "user_id" in response_data
    assert "employee_id" in response_data

    created_user = db.query(User).filter(User.email == "new.employee@example.com").first()
    created_employee = db.query(Employee).filter(Employee.id == response_data["employee_id"]).first()

    assert created_user is not None
    assert created_employee is not None
    assert created_employee.user_id == created_user.id
    assert created_user.must_change_password is True


def test_employee_onboarding_fails_with_duplicate_email(client, auth_headers, test_user):
    response = client.post(
        "/employees/onboarding",
        json = {
            "email": "test@example.com",
            "password": "temporary123",
            "role": "employee",
            "first_name": "Laura",
            "last_name": "Martin",
            "phone_number": "600111222",
            "max_weekly_hours": 40,
            "active": True
        },
        headers = auth_headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already registered"


def test_login_returns_must_change_password_for_onboarded_user(client, auth_headers):
    onboarding_response = client.post(
        "/employees/onboarding",
        json = {
            "email": "first.login@example.com",
            "password": "temporary123",
            "role": "employee",
            "first_name": "Mario",
            "last_name": "Sanchez",
            "phone_number": "600333444",
            "max_weekly_hours": 35,
            "active": True
        },
        headers = auth_headers
    )

    assert onboarding_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data = {
            "username": "first.login@example.com",
            "password": "temporary123"
        }
    )

    assert login_response.status_code == 200

    response_data = login_response.json()

    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"
    assert response_data["must_change_password"] is True


def test_change_password_updates_flag_and_allows_new_login(client, auth_headers, db):
    onboarding_response = client.post(
        "/employees/onboarding",
        json = {
            "email": "password.change@example.com",
            "password": "temporary123",
            "role": "employee",
            "first_name": "Lucia",
            "last_name": "Ruiz",
            "phone_number": "600555666",
            "max_weekly_hours": 30,
            "active": True
        },
        headers = auth_headers
    )

    assert onboarding_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data = {
            "username": "password.change@example.com",
            "password": "temporary123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    change_password_response = client.post(
        "/auth/change-password",
        json = {
            "current_password": "temporary123",
            "new_password": "newsecure123"
        },
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert change_password_response.status_code == 200
    assert change_password_response.json()["message"] == "Password updated successfully"

    updated_user = db.query(User).filter(User.email == "password.change@example.com").first()

    assert updated_user is not None
    assert updated_user.must_change_password is False

    new_login_response = client.post(
        "/auth/login",
        data = {
            "username": "password.change@example.com",
            "password": "newsecure123"
        }
    )

    assert new_login_response.status_code == 200
    assert new_login_response.json()["must_change_password"] is False


def test_change_password_fails_with_incorrect_current_password(client, auth_headers):
    onboarding_response = client.post(
        "/employees/onboarding",
        json = {
            "email": "wrong.current@example.com",
            "password": "temporary123",
            "role": "employee",
            "first_name": "Raul",
            "last_name": "Diaz",
            "phone_number": "600777888",
            "max_weekly_hours": 40,
            "active": True
        },
        headers = auth_headers
    )

    assert onboarding_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data = {
            "username": "wrong.current@example.com",
            "password": "temporary123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    change_password_response = client.post(
        "/auth/change-password",
        json = {
            "current_password": "wrongpassword",
            "new_password": "newsecure123"
        },
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert change_password_response.status_code == 400
    assert change_password_response.json()["detail"] == "Current password is incorrect"


def test_change_password_fails_when_new_password_matches_current_password(client, auth_headers):
    onboarding_response = client.post(
        "/employees/onboarding",
        json = {
            "email": "same.password@example.com",
            "password": "temporary123",
            "role": "employee",
            "first_name": "Elena",
            "last_name": "Gil",
            "phone_number": "600999000",
            "max_weekly_hours": 40,
            "active": True
        },
        headers = auth_headers
    )

    assert onboarding_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data = {
            "username": "same.password@example.com",
            "password": "temporary123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    change_password_response = client.post(
        "/auth/change-password",
        json = {
            "current_password": "temporary123",
            "new_password": "temporary123"
        },
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert change_password_response.status_code == 400
    assert change_password_response.json()["detail"] == "New password must be different from the current password"