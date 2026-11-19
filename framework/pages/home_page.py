from selenium.webdriver.common.by import By
from framework.pages.article_page import ArticlePage
from framework.pages.base_page import BasePage, by_testid
class HomePage(BasePage):
    path = "/"
    ARTICLE_LINKS = by_testid("article-link")

    def article_titles(self):
        self.find(self.HEADING)
        return [link.text for link in self.find_all(self.ARTICLE_LINKS)]

    def open_article(self, title):
        self.click((By.LINK_TEXT, title))
        page = ArticlePage(self.driver, self.base_url)
        page.find(page.TITLE)
        return page
