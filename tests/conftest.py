import os
import sys
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.core.database import Base, get_db

from tests.fixtures.auth import *
from tests.fixtures.planning import *


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args = {"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit = False,
    autoflush = False,
    bind = engine,
)


def override_get_db() -> Generator:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope = "session", autouse = True)
def create_test_database():
    Base.metadata.create_all(bind = engine)
    yield
    Base.metadata.drop_all(bind = engine)
    engine.dispose()
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture(scope = "function")
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind = connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope = "function")
def client(db):
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()