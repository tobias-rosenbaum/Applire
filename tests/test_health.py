"""
Iteration 0 — Walking Skeleton
Done when: docker compose up starts cleanly, GET /health returns 200.
"""
import requests


def test_health_returns_200(api):
    r = requests.get(f"{api}/health")
    assert r.status_code == 200


def test_health_body(api):
    r = requests.get(f"{api}/health")
    body = r.json()
    assert body["status"] == "ok"
    assert body["edition"] == "community"
