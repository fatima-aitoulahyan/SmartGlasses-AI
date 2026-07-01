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
    assert "model_ready" in response.json()


def test_recognize_no_file():
    response = client.post("/recognize")
    assert response.status_code == 422


def test_recognize_invalid_image():
    response = client.post(
        "/recognize",
        files={"file": ("test.jpg", b"not_an_image", "image/jpeg")}
    )
    assert response.status_code == 400


def test_recognize_returns_required_fields():
    sample = "tests/sample_bill.jpg"
    if not os.path.exists(sample):
        pytest.skip("No sample bill image — add tests/sample_bill.jpg")

    with open(sample, "rb") as f:
        response = client.post(
            "/recognize",
            files={"file": ("sample_bill.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "value"      in data
    assert "currency"   in data
    assert "confidence" in data
    assert data["currency"] == "MAD"
