import os

# Must run before any `app.*` import: app/config.py reads LLM_PROVIDER at import time via
# load_dotenv(), and the dev .env has it set to "openai" for manual real-provider testing.
# Tests must never construct a real network-calling provider (routes/interviews.py builds
# one module-level at import time), so force mock here first.
os.environ["LLM_PROVIDER"] = "mock"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.providers.mock_provider import MockProvider


@pytest.fixture()
def session():
    # In-memory SQLite per test - StaticPool so the single connection is shared across
    # the test (SQLAlchemy would otherwise open a fresh :memory: DB per connection, wiping
    # the schema).
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def provider():
    return MockProvider()
