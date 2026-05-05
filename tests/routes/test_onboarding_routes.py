from app.models.contract import Contract
from app.models.employee import Employee
from app.models.user import User


def test_employee_onboarding_creates_user_employee_and_contract(client, auth_headers, db):
    response = client.post(
        "/employees/onboarding",
        json = {
            "email": "new.employee@example.com",
            "password": "temporary123",
            "role": "employee",
            "first_name": "Laura",
            "last_name": "Martin",
            "phone_number": "600111222",
            "active": True,
            "contract": {
                "weekly_hours": 40,
                "daily_hours": 8,
                "min_days_off_per_week": 2,
                "work_monday": True,
                "work_tuesday": True,
                "work_wednesday": True,
                "work_thursday": True,
                "work_friday": True,
                "work_saturday": False,
                "work_sunday": False,
                "has_fixed_schedule": True,
                "preferred_start_time": "08:00:00",
                "preferred_end_time": "16:00:00",
                "active": True,
                "start_date": "2026-04-01",
                "end_date": None
            }
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
    assert response_data["phone_number"] == "600111222"
    assert response_data["active"] is True
    assert "user_id" in response_data
    assert "employee_id" in response_data
    assert "contract" in response_data

    assert response_data["contract"]["weekly_hours"] == 40
    assert response_data["contract"]["daily_hours"] == 8
    assert response_data["contract"]["min_days_off_per_week"] == 2
    assert response_data["contract"]["employee_id"] == response_data["employee_id"]
    assert response_data["contract"]["active"] is True
    assert response_data["contract"]["has_fixed_schedule"] is True
    assert response_data["contract"]["preferred_start_time"] == "08:00:00"
    assert response_data["contract"]["preferred_end_time"] == "16:00:00"

    created_user = db.query(User).filter(User.email == "new.employee@example.com").first()
    created_employee = db.query(Employee).filter(Employee.id == response_data["employee_id"]).first()
    created_contract = db.query(Contract).filter(Contract.employee_id == response_data["employee_id"]).first()

    assert created_user is not None
    assert created_employee is not None
    assert created_contract is not None
    assert created_employee.user_id == created_user.id
    assert created_user.must_change_password is True
    assert created_contract.weekly_hours == 40
    assert created_contract.daily_hours == 8
    assert created_contract.active is True


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
            "active": True,
            "contract": {
                "weekly_hours": 40,
                "daily_hours": 8,
                "min_days_off_per_week": 2,
                "work_monday": True,
                "work_tuesday": True,
                "work_wednesday": True,
                "work_thursday": True,
                "work_friday": True,
                "work_saturday": False,
                "work_sunday": False,
                "has_fixed_schedule": True,
                "preferred_start_time": "08:00:00",
                "preferred_end_time": "16:00:00",
                "active": True,
                "start_date": "2026-04-01",
                "end_date": None
            }
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
            "active": True,
            "contract": {
                "weekly_hours": 35,
                "daily_hours": 7,
                "min_days_off_per_week": 2,
                "work_monday": True,
                "work_tuesday": True,
                "work_wednesday": True,
                "work_thursday": True,
                "work_friday": True,
                "work_saturday": False,
                "work_sunday": False,
                "has_fixed_schedule": False,
                "preferred_start_time": None,
                "preferred_end_time": None,
                "active": True,
                "start_date": "2026-04-01",
                "end_date": None
            }
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
            "active": True,
            "contract": {
                "weekly_hours": 30,
                "daily_hours": 6,
                "min_days_off_per_week": 2,
                "work_monday": True,
                "work_tuesday": True,
                "work_wednesday": True,
                "work_thursday": True,
                "work_friday": True,
                "work_saturday": False,
                "work_sunday": False,
                "has_fixed_schedule": False,
                "preferred_start_time": None,
                "preferred_end_time": None,
                "active": True,
                "start_date": "2026-04-01",
                "end_date": None
            }
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
            "active": True,
            "contract": {
                "weekly_hours": 40,
                "daily_hours": 8,
                "min_days_off_per_week": 2,
                "work_monday": True,
                "work_tuesday": True,
                "work_wednesday": True,
                "work_thursday": True,
                "work_friday": True,
                "work_saturday": False,
                "work_sunday": False,
                "has_fixed_schedule": True,
                "preferred_start_time": "08:00:00",
                "preferred_end_time": "16:00:00",
                "active": True,
                "start_date": "2026-04-01",
                "end_date": None
            }
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
            "active": True,
            "contract": {
                "weekly_hours": 40,
                "daily_hours": 8,
                "min_days_off_per_week": 2,
                "work_monday": True,
                "work_tuesday": True,
                "work_wednesday": True,
                "work_thursday": True,
                "work_friday": True,
                "work_saturday": False,
                "work_sunday": False,
                "has_fixed_schedule": True,
                "preferred_start_time": "08:00:00",
                "preferred_end_time": "16:00:00",
                "active": True,
                "start_date": "2026-04-01",
                "end_date": None
            }
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


def test_employee_onboarding_creates_active_contract(client, auth_headers, db):
    response = client.post(
        "/employees/onboarding",
        json = {
            "email": "contract.check@example.com",
            "password": "temporary123",
            "role": "employee",
            "first_name": "Laura",
            "last_name": "Martin",
            "phone_number": "600111222",
            "active": True,
            "contract": {
                "weekly_hours": 40,
                "daily_hours": 8,
                "min_days_off_per_week": 2,
                "work_monday": True,
                "work_tuesday": True,
                "work_wednesday": True,
                "work_thursday": True,
                "work_friday": True,
                "work_saturday": False,
                "work_sunday": False,
                "has_fixed_schedule": True,
                "preferred_start_time": "08:00:00",
                "preferred_end_time": "16:00:00",
                "active": True,
                "start_date": "2026-04-01",
                "end_date": None
            }
        },
        headers = auth_headers
    )

    assert response.status_code == 201

    response_data = response.json()

    created_contract = db.query(Contract).filter(Contract.employee_id == response_data["employee_id"]).first()

    assert created_contract is not None
    assert created_contract.active is True
    assert created_contract.weekly_hours == 40
    assert created_contract.daily_hours == 8


def test_employee_onboarding_fails_with_invalid_contract(client, auth_headers):
    response = client.post(
        "/employees/onboarding",
        json = {
            "email": "invalid.contract@example.com",
            "password": "temporary123",
            "role": "employee",
            "first_name": "Invalid",
            "last_name": "Contract",
            "phone_number": "600111222",
            "active": True,
            "contract": {
                "weekly_hours": 40,
                "daily_hours": 8,
                "min_days_off_per_week": 2,
                "work_monday": True,
                "work_tuesday": True,
                "work_wednesday": True,
                "work_thursday": True,
                "work_friday": True,
                "work_saturday": False,
                "work_sunday": False,
                "has_fixed_schedule": True,
                "preferred_start_time": None,
                "preferred_end_time": None,
                "active": True,
                "start_date": "2026-04-01",
                "end_date": None
            }
        },
        headers = auth_headers
    )

    assert response.status_code == 422