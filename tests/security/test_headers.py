import pytest
import requests
from framework.config import EDITOR
pytestmark = [pytest.mark.security]
PATHS = ["/", "/login", "/search?q=exam", "/api/health", "/api/articles"]
@pytest.mark.parametrize("path", PATHS)
def test_security_headers_present(base_url, path):
    """SEC-TC-001: every response sends the baseline security headers."""
    headers = requests.get(base_url + path, timeout=10).headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "frame-ancestors 'none'" in headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

@pytest.mark.parametrize("path", PATHS)
def test_server_header_does_not_leak_versions(base_url, path):
    """SEC-TC-002: the Server header does not reveal framework or Python versions."""
    server = requests.get(base_url + path, timeout=10).headers.get("Server", "")
    assert "werkzeug" not in server.lower()
    assert "python" not in server.lower()

def test_session_cookie_flags(base_url):
    """SEC-TC-003: the session cookie is HttpOnly and SameSite=Lax."""
    response = requests.post(
    f"{base_url}/login", data=EDITOR, allow_redirects=False, timeout=10
    )
    assert response.status_code == 302
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie

def test_api_responses_are_not_cached(base_url):
    """SEC-TC-004: API responses send Cache-Control: no-store."""
    response = requests.get(f"{base_url}/api/articles", timeout=10)
    assert response.headers.get("Cache-Control") == "no-store"
