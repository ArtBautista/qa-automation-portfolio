import uuid
import pytest
from framework.config import EDITOR
from framework.pages import LoginPage

pytestmark = [pytest.mark.ui]

@pytest.mark.smoke
def test_editor_can_sign_in(driver, base_url):
    """UI-TC-001: valid credentials show the success message and the user name."""
    home = LoginPage(driver, base_url).open().login(**EDITOR)
    assert home.flash_message() == "Signed in successfully."
    assert home.signed_in_user_text() == "Signed in as editor"


@pytest.mark.parametrize(
"username, password",
[("editor", "wrong-password"), (f"ghost-{uuid.uuid4().hex[:6]}", "Editor#2026")],
ids=["wrong-password", "unknown-user"],
)

def test_invalid_credentials_show_error(driver, base_url, username, password):
    """UI-TC-002: invalid credentials keep the user on /login with a generic error."""
    page = LoginPage(driver, base_url).open()
    page.submit_credentials(username, password)
    assert page.error_message() == "Invalid username or password."
    assert driver.current_url.endswith("/login")

def test_login_fields_are_required(driver, base_url):
    """UI-TC-003: username and password carry the HTML required attribute."""
    page = LoginPage(driver, base_url).open()
    assert page.is_field_required(page.USERNAME)
    assert page.is_field_required(page.PASSWORD)

def test_sign_out(editor_home):
    """UI-TC-004: signing out shows the Sign in link again."""
    editor_home.logout()
    assert editor_home.flash_message() == "Signed out."
    assert editor_home.is_visible(editor_home.NAV_LOGIN)
