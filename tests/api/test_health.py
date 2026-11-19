import pytest

pytestmark = [pytest.mark.api]

@pytest.mark.smoke
def test_health_endpoints_reports_ok(anon_api):
    """API-TC-001: /api/health returns 200, JSON body and responds in under 500 ms."""
    response = anon_api.get("/api/health")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.json()["status"] == "ok"
    assert response.elapsed.total_seconds() < 0.5
