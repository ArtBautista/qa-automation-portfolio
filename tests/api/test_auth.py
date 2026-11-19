import uuid

import pytest

from framework.config import EDITOR

pytestmark = [pytest.mark.api]

@pytest.mark.smoke
def test_valid_credentials_return_token(anon_api):
    """API-TC-030: valid editor credentials return a bearer token."""
    response = anon_api.post("/api/auth/token", json=EDITOR)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["token"], str) and len(body["token"]) > 20
    assert body["expires_in"] == 3600

@pytest.mark.parametrize(
    "credentials",
    [
        {"username": "editor", "password": "wrong-password"},
        {"username": f"ghost-{uuid.uuid4().hex[:6]}", "password": "Editor#2026"},
        {},
    ],
    ids=["wrong-password", "unknown-user", "empty-body"],
)
def test_invalid_credentials_are_rejected(anon_api, credentials):
    """API-TC-031: invalid credentials return 401 and no token."""
    response = anon_api.post("/api/auth/token", json=credentials)
    assert response.status_code == 401
    assert "token" not in response.json()
def test_viewer_cannot_create_article(viewer_api, unique_title):
    """API-TC-033: a viewer token gets 403 on POST /api/articles."""
    response = viewer_api.post(
    "/api/articles", json={"title": unique_title, "body": "Not allowed.", "status": "draft"}
    )
    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"
def test_create_without_token_is_unauthorised(anon_api, unique_title):
    """API-TC-034: POST /api/articles without a token returns 401 missing_token."""
    response = anon_api.post("/api/articles", json={"title": unique_title, "body": "x"})
    assert response.status_code == 401
    assert response.json()["error"] == "missing_token"
