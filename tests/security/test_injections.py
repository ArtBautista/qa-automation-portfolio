import pytest
import requests
pytestmark = [pytest.mark.security]
XSS_PAYLOAD = "<script>alert('xss')</script>"
SQLI_PAYLOADS = [
"' OR '1'='1",
"' OR 1=1 --",
"'; DROP TABLE articles; --",
'" OR ""="',
]
def test_reflected_xss_is_escaped(base_url):
    """SEC-TC-010: a script tag in ?q= is HTML-escaped, not executed."""
    response = requests.get(f"{base_url}/search", params={"q": XSS_PAYLOAD}, timeout=10)
    assert response.status_code == 200
    assert XSS_PAYLOAD not in response.text
    assert "&lt;script&gt;" in response.text
def test_stored_xss_is_escaped(base_url, editor_api):
    """SEC-TC-013: HTML saved in an article title is escaped on the article page."""
    payload = "<img src=x onerror=alert(1)>"
    article = editor_api.post(
    "/api/articles", json={"title": payload, "body": "Stored XSS probe.", "status": "published"}
    ).json()
    page = requests.get(f"{base_url}/articles/{article['id']}", timeout=10)

    assert payload not in page.text
    assert "&lt;img src=x onerror=alert(1)&gt;" in page.text
    editor_api.delete(f"/api/articles/{article['id']}")

@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
def test_sql_injection_in_api_search(anon_api, payload):
    """SEC-TC-011: SQL meta-characters in ?q= are treated as text (no 500, no data dump)."""
    response = anon_api.get("/api/articles", params={"q": payload})

    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert anon_api.get("/api/articles").status_code == 200 # table still exists
@pytest.mark.parametrize("username", ["editor' --", "' OR '1'='1' --", "editor'/*"])
def test_sql_injection_cannot_bypass_login(anon_api, username):
    """SEC-TC-012: SQL injection in the username does not return a token."""
    response = anon_api.post(
        "/api/auth/token", json={"username": username, "password": "anything"}
    )

    assert response.status_code == 401
    assert "token" not in response.json()
