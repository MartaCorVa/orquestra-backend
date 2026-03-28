import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import hash_password


@pytest.fixture
def test_user(db: Session):
    user = User(
        email = "test@example.com",
        password = hash_password("testpassword"),
        role = "admin",
        active = True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def employee_user(db: Session):
    user = User(
        email = "employee@example.com",
        password = hash_password("testpassword"),
        role = "employee",
        active = True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def inactive_user(db: Session):
    user = User(
        email = "inactive@example.com",
        password = hash_password("testpassword"),
        role = "admin",
        active = False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def auth_headers(client, test_user):
    response = client.post(
        "/auth/login",
        data = {
            "username": "test@example.com",
            "password": "testpassword",
        }
    )

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def employee_auth_headers(client, employee_user):
    response = client.post(
        "/auth/login",
        data = {
            "username": "employee@example.com",
            "password": "testpassword",
        },
    )

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def inactive_auth_headers(client, inactive_user):
    response = client.post(
        "/auth/login",
        data = {
            "username": "inactive@example.com",
            "password": "testpassword",
        },
    )

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }