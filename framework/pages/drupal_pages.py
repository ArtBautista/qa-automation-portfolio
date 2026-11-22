"""Page Objects for a standard Drupal 10 install (Olivero front-end theme, Claro admin theme)."""
from selenium.webdriver.common.by import By

from framework.pages.base_page import BasePage

MESSAGES = (By.CSS_SELECTOR, "[data-drupal-messages]")


class DrupalLoginPage(BasePage):
    path = "/user/login"
    USERNAME = (By.ID, "edit-name")
    PASSWORD = (By.ID, "edit-pass")
    SUBMIT = (By.ID, "edit-submit")

    def login(self, username, password):
        self.type(self.USERNAME, username)
        self.type(self.PASSWORD, password)
        self.click(self.SUBMIT)

    def login_successfully(self, username, password):
        """Sign in and wait until Drupal redirects away from the login page."""
        self.login(username, password)
        self.wait.until(lambda driver: "/user/login" not in driver.current_url)

    def messages(self):
        return self.text_of(MESSAGES)


class DrupalAddArticlePage(BasePage):
    path = "/node/add/article"
    TITLE = (By.ID, "edit-title-0-value")
    SAVE = (By.ID, "edit-submit")

    def create(self, title):
        self.type(self.TITLE, title)
        self.click(self.SAVE)
        return self.text_of(MESSAGES)
