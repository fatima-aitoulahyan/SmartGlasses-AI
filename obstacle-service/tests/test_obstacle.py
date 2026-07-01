import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_detect_no_file():
    response = client.post("/detect")
    assert response.status_code == 422  # missing file


def test_detect_invalid_image():
    response = client.post(
        "/detect",
        files={"file": ("test.jpg", b"not_an_image", "image/jpeg")}
    )
    assert response.status_code == 400


def test_detect_valid_image():
    sample = "tests/sample.jpg"
    if not os.path.exists(sample):
        pytest.skip("No sample image found — add tests/sample.jpg")

    with open(sample, "rb") as f:
        response = client.post(
            "/detect",
            files={"file": ("sample.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "alert_message" in data
    assert "objects"       in data
    assert "distances"     in data
