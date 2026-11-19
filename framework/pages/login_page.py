from framework.pages.base_page import BasePage, by_testid
from framework.pages.home_page import HomePage

class LoginPage(BasePage):
    path = "/login"
    USERNAME = by_testid("username-input")
    PASSWORD = by_testid("password-input")
    SUBMIT = by_testid("login-submit")
    ERROR = by_testid("login-error")

    def submit_credentials(self, username, password):
        self.type(self.USERNAME, username)
        self.type(self.PASSWORD, password)
        self.click(self.SUBMIT)

    def login(self, username, password):
        """Happy path: sign in and land on the home page."""
        self.submit_credentials(username, password)
        home = HomePage(self.driver, self.base_url)
        home.find(home.FLASH)
        return home

    def error_message(self):
        return self.text_of(self.ERROR)

    def is_field_required(self, locator):
        return self.find(locator).get_attribute("required") is not None
