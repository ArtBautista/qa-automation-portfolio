from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def by_testid(value):
    return (By.CSS_SELECTOR, f'[data-testid="{value}"]')

class BasePage:
    path = "/"
    HEADING = (By.TAG_NAME, "h1")
    FLASH = by_testid("flash")
    NAV_USER = by_testid("nav-user")
    NAV_LOGIN = by_testid("nav-login")
    NAV_NEW_ARTICLE = by_testid("nav-new-article")
    LOGOUT_BUTTON = by_testid("logout-button")
    def __init__(self, driver, base_url, timeout=10):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, timeout)
    # ------------------------------------------------------------ navigation
    def open(self):
        self.driver.get(self.base_url + self.path)
        self.find(self.HEADING)
        return self
    # ------------------------------------------------------------ element helpers
    def find(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def find_all(self, locator):
        return self.driver.find_elements(*locator)

    def click(self, locator):
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def type(self, locator, text):
        element = self.find(locator)
        element.clear()
        element.send_keys(text)

    def text_of(self, locator):
        return self.find(locator).text

    def is_visible(self, locator, timeout=2):
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    # ------------------------------------------------------------ shared page parts
    @property
    def heading(self):
        return self.text_of(self.HEADING)

    def flash_message(self):
        return self.text_of(self.FLASH)

    def signed_in_user_text(self):
        return self.text_of(self.NAV_USER)

    def logout(self):
        self.click(self.LOGOUT_BUTTON)
        self.find(self.NAV_LOGIN)
