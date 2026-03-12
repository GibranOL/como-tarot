"""
Shared PostgreSQL fixtures for all integration tests.

WHY: One engine, one schema lifecycle per the CLAUDE.md Step 6 rule.
     Using real PostgreSQL (not SQLite) ensures we catch DB-level bugs
     (type coercion, constraint enforcement) that SQLite silently ignores.

Usage:
    Set TEST_DATABASE_URL before running integration tests:
        export TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/cosmotarot_test

    With Docker:
        docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=test -e POSTGRES_DB=cosmotarot_test postgres:16
        export TEST_DATABASE_URL=postgresql://postgres:test@localhost:5432/cosmotarot_test
"""
import os
import pytest
from sqlmodel import SQLModel, Session, create_engine

import app.models  # noqa: F401 — registers all models with SQLModel.metadata before create_all


@pytest.fixture(name="test_engine", scope="session")
def test_engine_fixture():
    """
    WHAT: Session-scoped PostgreSQL engine shared by all integration tests.
    WHY: A single engine avoids the overhead of reconnecting per test module
         and ensures schema is created once and torn down at the end.

    Skips all integration tests if TEST_DATABASE_URL is not set.
    Set it to a real PostgreSQL URL before running the integration suite.
    """
    db_url = os.environ.get("TEST_DATABASE_URL")
    if not db_url:
        pytest.skip(
            "TEST_DATABASE_URL not set — skipping integration tests. "
            "Set TEST_DATABASE_URL=postgresql://user:pass@host/dbname to enable."
        )

    engine = create_engine(db_url, echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="db_session")
def db_session_fixture(test_engine):
    """
    WHAT: Yields a database session per test function.
    WHY: Each test should operate on a fresh session to avoid state bleeding
         between tests. The shared engine ensures tables are never re-created.
    """
    with Session(test_engine) as session:
        yield session
