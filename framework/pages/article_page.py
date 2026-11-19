from framework.pages.base_page import BasePage, by_testid

class ArticlePage(BasePage):
    TITLE = by_testid("article-title")
    STATUS = by_testid("article-status")
    BODY = by_testid("article-body")
    @property
    def title(self):
        return self.text_of(self.TITLE)

    @property
    def status(self):
        return self.text_of(self.STATUS)

    @property
    def body(self):
        return self.text_of(self.BODY)

    @property
    def article_id(self):
        return int(self.driver.current_url.rstrip("/").split("/")[-1])
