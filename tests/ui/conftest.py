import pytest

from framework.config import EDITOR, VIEWER
from framework.pages import LoginPage

@pytest.fixture
def editor_home(driver, base_url):
    """A browser already signed in as the editor, sitting on the home page."""
    return LoginPage(driver, base_url).open().login(**EDITOR)

@pytest.fixture
def viewer_home(driver, base_url):
    return LoginPage(driver, base_url).open().login(**VIEWER)
