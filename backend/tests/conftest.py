"""
Shared test fixtures for CosmoTarot.
One engine, one set of fixtures, one dependency override (per CLAUDE.md rules).
Expanded in Step 6.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.db.database import get_session


@pytest.fixture(name="engine", scope="session")
def engine_fixture():
    """
    Session-scoped in-memory SQLite engine for unit tests only.
    Integration tests use PostgreSQL — see tests/integration/conftest.py (Step 6).
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    """Yield a test database session."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session):
    """FastAPI test client with DB session override."""
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
