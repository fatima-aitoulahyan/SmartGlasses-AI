import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "SmartGlasses AI" in response.json()["project"]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_invalid_mode():
    with open("tests/sample.jpg", "rb") as f:
        response = client.post(
            "/analyze?mode=invalid",
            files={"file": ("test.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 502
    assert response.json()["success"] is False
