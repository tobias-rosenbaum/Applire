"""
Unit test configuration.

Overrides the session-scoped docker_environment autouse fixture from the
parent conftest.py so that unit tests run without starting Docker.
"""
import os

import pytest

# Provide required settings so config.py can be imported without a real DB.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")


@pytest.fixture(scope="session", autouse=True)
def docker_environment():
    """Unit tests do not require Docker."""
    yield
