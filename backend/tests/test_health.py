from fastapi.testclient import TestClient

from app.main import app


def test_health_is_public_and_lightweight() -> None:
    """The Render warm-up route must not need database or OpenAI access."""
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "construction-safety-backend",
    }
