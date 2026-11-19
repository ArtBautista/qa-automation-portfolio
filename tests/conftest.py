"""Shared fixtures and hooks for API, UI and security tests."""
import base64
import os
import re
import uuid
from pathlib import Path
import pytest
import requests
from framework.api_client import ApiClient, get_token
from framework.config import BASE_URL, EDITOR, VIEWER
SCREENSHOT_DIR = Path("reports/screenshots")
def pytest_addoption(parser):
    parser.addoption(
        "--browser",
        default=os.environ.get("BROWSER", "chrome"),
        choices=["chrome", "firefox", "edge"],
        help="Browser for UI tests",
        )
    parser.addoption(
        "--headless",
        action="store_true",
        default=os.environ.get("HEADLESS") == "1",
        help="Run browsers without a window",
    )
    parser.addoption(
        "--remote-url",
        default=os.environ.get("SELENIUM_REMOTE_URL"),
        help="Selenium Grid URL, e.g. http://localhost:4444",
    )
# ---------------------------------------------------------------- API fixtures
@pytest.fixture(scope="session")
def base_url():
    try:
        requests.get(f"{BASE_URL}/api/health", timeout=5).raise_for_status()
    except requests.RequestException as exc:
        pytest.exit(f"Content Portal is not reachable at {BASE_URL}: {exc}", returncode=2)
    return BASE_URL
@pytest.fixture(scope="session")
def anon_api(base_url):
    return ApiClient(base_url)
@pytest.fixture(scope="session")
def editor_api(base_url):
    return ApiClient(base_url, token=get_token(base_url, EDITOR))
@pytest.fixture(scope="session")
def viewer_api(base_url):
    return ApiClient(base_url, token=get_token(base_url, VIEWER))
@pytest.fixture
def unique_title():
    return f"QA Auto {uuid.uuid4().hex[:8]}"
@pytest.fixture
def created_article(editor_api, unique_title):
    response = editor_api.post(
        "/api/articles",
        json={"title": unique_title, "body": "Created by a pytest fixture.", "status": "published"},
    )
    assert response.status_code == 201, response.text
    article = response.json()
    yield article
    editor_api.delete(f"/api/articles/{article['id']}")
# ---------------------------------------------------------------- UI fixtures
@pytest.fixture
def driver(request):
    from framework.driver_factory import build_driver
    browser_driver = build_driver(
        browser=request.config.getoption("--browser"),
        headless=request.config.getoption("--headless"),
        remote_url=request.config.getoption("--remote-url"),
    )
    yield browser_driver
    browser_driver.quit()
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """On a failed UI test: save a PNG and embed it in the pytest-html report."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    browser_driver = item.funcargs.get("driver")
    if browser_driver is None:
        return
    screenshot_b64 = browser_driver.get_screenshot_as_base64()
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w.-]", "_", item.nodeid)
    (SCREENSHOT_DIR / f"{safe_name}.png").write_bytes(base64.b64decode(screenshot_b64))
    pytest_html = item.config.pluginmanager.getplugin("html")
    if pytest_html is not None:
        extras = getattr(report, "extras", [])
        extras.append(pytest_html.extras.image(screenshot_b64))
        report.extras = extras
