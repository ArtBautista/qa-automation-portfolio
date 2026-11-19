import uuid
import pytest
from framework.pages import EditorPage, HomePage, SearchPage

pytestmark = [pytest.mark.ui]

@pytest.mark.smoke
def test_home_lists_published_but_not_draft(driver, base_url):
    """UI-TC-010: home page shows published articles and hides drafts."""
    titles = HomePage(driver, base_url).open().article_titles()
    assert "Welcome to the Content Portal" in titles
    assert "Draft: Upcoming Features" not in titles

def test_open_article_from_home(driver, base_url):
    """UI-TC-011: clicking a card opens the article with its title and body."""
    article = HomePage(driver, base_url).open().open_article("Exam Preparation Tips")
    assert article.title == "Exam Preparation Tips"
    assert "past papers" in article.body

@pytest.mark.smoke
def test_editor_creates_published_article(editor_home, driver, base_url, editor_api):
    """UI-TC-012: editor creates an article end to end and it appears on the home page."""
    title = f"UI Article {uuid.uuid4().hex[:8]}"

    article = EditorPage(driver, base_url).open().create_article(title, "Written by Selenium.")
    article_id = article.article_id  # read it now, while the browser is still on /articles/{id}

    try:
        assert article.flash_message() == "Article created."
        assert article.title == title
        assert article.status == "published"
        assert title in HomePage(driver, base_url).open().article_titles()
    finally:
        editor_api.delete(f"/api/articles/{article_id}")

@pytest.mark.parametrize(
    "title, expected_error",
    [("", "Title is required."), ("ab", "Title must be 3-120 characters.")],
    ids=["empty-title", "two-char-title"],
)
def test_editor_title_validation(editor_home, driver, base_url, title, expected_error):
    """UI-TC-013: invalid titles show an inline error and the article is not saved."""
    editor = EditorPage(driver, base_url).open()
    editor.fill(title, "Body text", "draft")
    editor.save()
    assert editor.title_error() == expected_error
    assert editor.heading == "New article"

def test_viewer_has_no_new_article_link(viewer_home):
    """UI-TC-014: a viewer does not see the New article link."""
    assert not viewer_home.is_visible(viewer_home.NAV_NEW_ARTICLE, timeout=1)

@pytest.mark.parametrize(
"term, expected_title",
[("Exam", "Exam Preparation Tips"), ("welcome", "Welcome to the Content Portal")],
)

def test_search_finds_articles(driver, base_url, term, expected_title):
    """UI-TC-015: search is case-insensitive and returns matching titles (data-driven)."""
    page = SearchPage(driver, base_url).open().search(term)
    assert expected_title in page.result_titles()

def test_search_with_no_results(driver, base_url):
    """UI-TC-016: a term with no matches shows a zero-results summary."""
    page = SearchPage(driver, base_url).open().search("zzz-no-match")
    assert page.summary().startswith("0 results")
    assert page.result_titles() == []
