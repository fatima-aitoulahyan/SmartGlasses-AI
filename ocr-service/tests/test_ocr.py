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


def test_read_no_file():
    response = client.post("/read")
    assert response.status_code == 422


def test_read_invalid_image():
    response = client.post(
        "/read",
        files={"file": ("test.jpg", b"not_an_image", "image/jpeg")}
    )
    assert response.status_code == 400


def test_read_returns_required_fields():
    sample = "tests/sample_text.jpg"
    if not os.path.exists(sample):
        pytest.skip("No sample image — add tests/sample_text.jpg")

    with open(sample, "rb") as f:
        response = client.post(
            "/read",
            files={"file": ("sample_text.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "text"       in data
    assert "language"   in data
    assert "script"     in data
    assert "confidence" in data


def test_script_detector_latin():
    from script_detector import ScriptDetector
    sd = ScriptDetector()
    assert sd.detect_from_text("Hello world") == "latin"


def test_script_detector_arabic():
    from script_detector import ScriptDetector
    sd = ScriptDetector()
    assert sd.detect_from_text("مرحبا بالعالم") == "arabic"


def test_lang_identifier_fr():
    from lang_identifier import LangIdentifier
    li = LangIdentifier()
    assert li.identify("Bonjour le monde", "latin") == "fr"


def test_lang_identifier_en():
    from lang_identifier import LangIdentifier
    li = LangIdentifier()
    assert li.identify("Hello world this is English text", "latin") == "en"


def test_lang_identifier_arabic_script():
    from lang_identifier import LangIdentifier
    li = LangIdentifier()
    assert li.identify("أي نص", "arabic") == "ar"
