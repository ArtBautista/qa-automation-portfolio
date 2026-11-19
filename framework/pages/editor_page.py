from selenium.webdriver.support.ui import Select
from framework.pages.article_page import ArticlePage
from framework.pages.base_page import BasePage, by_testid

class EditorPage(BasePage):
    path = "/editor/articles/new"
    TITLE = by_testid("title-input")
    BODY = by_testid("body-input")
    STATUS = by_testid("status-select")
    SAVE = by_testid("save-article")
    TITLE_ERROR = by_testid("title-error")
    BODY_ERROR = by_testid("body-error")

    def fill(self, title, body, status="draft"):
        self.type(self.TITLE, title)
        self.type(self.BODY, body)
        Select(self.find(self.STATUS)).select_by_value(status)
    def save(self):
        self.click(self.SAVE)
    def create_article(self, title, body, status="published"):
        self.fill(title, body, status)
        self.save()
        page = ArticlePage(self.driver, self.base_url)
        page.find(page.TITLE)
        return page
    def title_error(self):
        return self.text_of(self.TITLE_ERROR)
