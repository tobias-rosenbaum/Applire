"""
Unit test conftest — overrides the session-scoped docker_environment fixture
from the parent conftest so unit tests can run without a live Docker environment.
"""
import pytest


@pytest.fixture(scope="session", autouse=True)
def docker_environment():
    """No-op override: unit tests use TestClient and need no running services."""
    yield
