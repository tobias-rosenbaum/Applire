"""
Shared fixtures for Apliqa integration tests (patched for container execution).
Services are already running, so we just skip the docker management.
"""
import time
import pytest
import requests

# Use backend service name for intra-container communication
API_BASE = "http://backend:8000"
_READY_TIMEOUT = 30  # seconds

def _wait_for_api() -> None:
    deadline = time.time() + _READY_TIMEOUT
    while time.time() < deadline:
        try:
            r = requests.get(f"{API_BASE}/health", timeout=2)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"API did not become ready within {_READY_TIMEOUT}s")

@pytest.fixture(scope="session", autouse=True)
def docker_environment():
    """Just wait for the API, services are already running."""
    _wait_for_api()
    yield

@pytest.fixture(scope="session")
def api():
    return API_BASE
