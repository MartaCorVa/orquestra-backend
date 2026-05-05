from app.core.config import ALGORITHM, SECRET_KEY
from app.core.security import create_access_token, hash_password, verify_password


def test_hash_password():
    password = "mypassword"
    hashed = hash_password(password)

    assert hashed != password
    assert isinstance(hashed, str)


def test_verify_password_correct():
    password = "mypassword"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    password = "mypassword"
    hashed = hash_password(password)

    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    data = {"sub": "user1"}
    token = create_access_token(data)

    assert token is not None
    assert isinstance(token, str)
    

from jose import jwt

def test_create_access_token_contains_data():
    data = {"sub": "user1"}
    token = create_access_token(data)

    decoded = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])

    assert decoded["sub"] == "user1"
    assert "exp" in decoded