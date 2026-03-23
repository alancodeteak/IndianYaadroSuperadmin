from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoints_are_available():
    client = TestClient(app)

    health = client.get("/health")
    live = client.get("/health/live")
    ready = client.get("/health/ready")
    full = client.get("/health/full")

    assert health.status_code == 200
    assert live.status_code == 200
    assert ready.status_code == 200
    assert full.status_code == 200
