from framework.pages.base_page import BasePage, by_testid

class SearchPage(BasePage):
    path = "/search"
    QUERY = by_testid("search-input")
    SUBMIT = by_testid("search-submit")
    SUMMARY = by_testid("search-summary")
    RESULTS = by_testid("search-result")

    def search(self, term):
        self.type(self.QUERY, term)
        self.click(self.SUBMIT)
        self.find(self.SUMMARY)
        return self

    def summary(self):
        return self.text_of(self.SUMMARY)

    def result_titles(self):
        return [item.text for item in self.find_all(self.RESULTS)]
