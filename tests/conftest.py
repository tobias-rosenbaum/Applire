"""
Shared fixtures for Apliqa integration tests.

Setup: docker compose build + up, wait for API readiness, run migrations.
Teardown: containers are left running so the developer can inspect state.
To stop: docker compose down
"""
import os
import subprocess
import time
from pathlib import Path

import pytest
import requests

PROJECT_ROOT = Path(__file__).parent.parent
API_BASE = "http://localhost:8001"
_READY_TIMEOUT = 120  # seconds

# Rootless Docker uses a per-user socket; fall back to the system socket.
_uid = os.getuid()
_rootless_sock = Path(f"/run/user/{_uid}/docker.sock")
_DOCKER_ENV = {
    **os.environ,
    "DOCKER_HOST": f"unix://{_rootless_sock}" if _rootless_sock.exists() else "unix:///var/run/docker.sock",
}


def _docker_compose(*args: str) -> None:
    subprocess.run(
        ["docker", "compose", *args],
        cwd=PROJECT_ROOT,
        env=_DOCKER_ENV,
        check=True,
    )


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
    # Only build and start the services the API tests need.
    # The frontend service is excluded: npm install + next build takes several
    # minutes and is not required for backend integration tests.
    _docker_compose("build", "backend", "postgres")
    _docker_compose("up", "-d", "postgres", "backend")
    _wait_for_api()
    _docker_compose("exec", "backend", "python", "-m", "alembic", "upgrade", "head")
    yield
    # Containers intentionally left running after tests.
    # Run `docker compose down` manually to stop.


@pytest.fixture(scope="session")
def api():
    return API_BASE
