import uuid

import pytest
import requests

from framework.config import VIEWER

pytestmark = [pytest.mark.security]
def test_tampered_token_is_rejected(editor_api, base_url):
    """SEC-TC-020: changing one character of a valid token returns 401 invalid_token."""
    token = editor_api.session.headers["Authorization"].removeprefix("Bearer ")
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    response = requests.post(
    f"{base_url}/api/articles",
        json={"title": "Tampered", "body": "x"},
        headers={"Authorization": f"Bearer {tampered}"},
        timeout=10,
    )
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_token"

def test_brute_force_lockout(anon_api):
    """SEC-TC-021: the 6th failed login for a user within 5 minutes returns 429."""
    username = f"brute-{uuid.uuid4().hex[:8]}"
    credentials = {"username": username, "password": "wrong"}
    statuses = [anon_api.post("/api/auth/token", json=credentials).status_code for _ in range(6)]
    assert statuses == [401, 401, 401, 401, 401, 429]

def test_viewer_cannot_open_editor_page(base_url):
    """SEC-TC-022: a signed-in viewer gets 403 on the editor page."""
    browser = requests.Session()
    browser.post(f"{base_url}/login", data=VIEWER, timeout=10)
    response = browser.get(f"{base_url}/editor/articles/new", timeout=10)
    assert response.status_code == 403

def test_anonymous_user_redirected_to_login(base_url):
    """SEC-TC-023: an anonymous user is redirected from the editor page to /login."""
    response = requests.get(
        f"{base_url}/editor/articles/new", allow_redirects=False, timeout=10
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

def test_draft_not_exposed_to_anonymous(anon_api, editor_api):
    """SEC-TC-024: a draft article returns 404 to anonymous API and web requests."""
    draft_id = editor_api.get("/api/articles", params={"status": "draft"}).json()["items"][0]["id"]
    assert anon_api.get(f"/api/articles/{draft_id}").status_code == 404
    assert requests.get(f"{anon_api.base_url}/articles/{draft_id}", timeout=10).status_code == 404

def test_malformed_json_does_not_leak_stack_trace(editor_api):
    """SEC-TC-025: malformed JSON returns a clean 400 without a traceback."""
    response = editor_api.post(
        "/api/articles", data="{not valid json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400
    assert response.json() == {"error": "invalid_json"}
    assert "Traceback" not in response.text
