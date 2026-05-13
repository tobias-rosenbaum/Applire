"""
Unit test conftest — overrides the session-scoped docker_environment fixture
from the parent conftest so unit tests can run without a live Docker environment.
Sets DATABASE_URL before any app module is imported to satisfy the Settings validator.
"""
import os

# Must be set before app modules are imported (pydantic Settings validates at import time)
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

import pytest


@pytest.fixture(scope="session", autouse=True)
def docker_environment():
    """No-op override: unit tests use TestClient and need no running services."""
    yield
