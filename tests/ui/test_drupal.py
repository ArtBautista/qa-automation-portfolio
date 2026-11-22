"""Optional: runs against a local Drupal 10 site started with drupal/docker-compose.yml."""
import os
import uuid

import pytest

from framework.pages.drupal_pages import DrupalAddArticlePage, DrupalLoginPage

DRUPAL_URL = os.environ.get("DRUPAL_URL", "").rstrip("/")
DRUPAL_USER = os.environ.get("DRUPAL_USER", "admin")
DRUPAL_PASS = os.environ.get("DRUPAL_PASS", "")

pytestmark = [
    pytest.mark.ui,
    pytest.mark.drupal,
    pytest.mark.skipif(not DRUPAL_URL, reason="Set DRUPAL_URL to run Drupal tests"),
]


def test_drupal_rejects_bad_password(driver):
    """DRU-TC-001: Drupal shows an error for a wrong password."""
    page = DrupalLoginPage(driver, DRUPAL_URL).open()

    page.login(DRUPAL_USER, "definitely-wrong")

    assert "Unrecognized username or password" in page.messages()


def test_drupal_editor_creates_article(driver):
    """DRU-TC-002: an admin creates an Article node and sees the confirmation message."""
    DrupalLoginPage(driver, DRUPAL_URL).open().login_successfully(DRUPAL_USER, DRUPAL_PASS)
    title = f"Selenium article {uuid.uuid4().hex[:6]}"

    message = DrupalAddArticlePage(driver, DRUPAL_URL).open().create(title)

    assert f"Article {title} has been created" in message
    assert title in driver.title
