"""Automated tests for health and readiness endpoints.
"""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "docs" in data


def test_health_check(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data
    assert "version" in data


def test_readiness_check(client: TestClient):
    response = client.get("/api/v1/readiness")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "dependencies" in data
    assert data["dependencies"]["database"] == "connected"
