from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dashboard_home() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Plateforme de digitalisation" in response.text
