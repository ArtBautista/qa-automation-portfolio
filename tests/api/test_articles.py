import pytest
pytestmark = [pytest.mark.api]
ARTICLE_SCHEMA = {
    "id": int,
    "title": str,
    "body": str,
    "status": str,
    "author": str,
    "created_at": float,
}
def assert_matches_schema(article):
    assert set(article) == set(ARTICLE_SCHEMA), f"Unexpected keys: {sorted(article)}"
    for key, expected_type in ARTICLE_SCHEMA.items():
        assert isinstance(article[key], expected_type), f"{key} should be {expected_type}"

# ---------------------------------------------------------------- read
@pytest.mark.smoke
def test_list_returns_only_published_articles(anon_api):
    """API-TC-010: anonymous list contains only published articles."""
    response = anon_api.get("/api/articles")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == len(body["items"]) > 0
    assert {item["status"] for item in body["items"]} == {"published"}

def test_limit_parameter_is_respected(anon_api):
    """API-TC-011: ?limit=1 returns at most one article."""
    response = anon_api.get("/api/articles", params={"limit": 1})
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1

@pytest.mark.parametrize("limit", ["0", "101", "-5", "abc"])
def test_invalid_limit_returns_400(anon_api, limit):
    """API-TC-012: limit outside 1-100 or non-numeric returns 400 invalid_limit."""
    response = anon_api.get("/api/articles", params={"limit": limit})
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_limit"

def test_drafts_require_editor_token(anon_api):
    """API-TC-013: anonymous ?status=draft returns 401."""
    response = anon_api.get("/api/articles", params={"status": "draft"})
    assert response.status_code == 401

def test_editor_can_list_all_statuses(editor_api):
    """API-TC-014: editor ?status=all includes draft articles."""
    response = editor_api.get("/api/articles", params={"status": "all", "limit": 100})

    assert response.status_code == 200
    assert "draft" in {item["status"] for item in response.json()["items"]}

def test_get_article_matches_schema(anon_api, created_article):
    """API-TC-015: GET /api/articles/{id} returns the documented schema."""
    response = anon_api.get(f"/api/articles/{created_article['id']}")
    assert response.status_code == 200
    assert_matches_schema(response.json())

def test_missing_article_returns_404_json(anon_api):
    """API-TC-016: unknown id returns 404 with a JSON error body."""
    response = anon_api.get("/api/articles/999999")
    assert response.status_code == 404
    assert response.json() == {"error": "not_found"}
# ---------------------------------------------------------------- create
@pytest.mark.smoke
def test_create_article(editor_api, anon_api, unique_title):
    """API-TC-020: editor creates a published article; it is readable afterwards."""
    payload = {"title": unique_title, "body": "Body text.", "status": "published"}
    response = editor_api.post("/api/articles", json=payload)
    assert response.status_code == 201
    article = response.json()
    assert_matches_schema(article)
    assert response.headers["Location"] == f"/api/articles/{article['id']}"
    assert article["title"] == unique_title
    assert article["author"] == "editor"
    assert anon_api.get(f"/api/articles/{article['id']}").status_code == 200
    editor_api.delete(f"/api/articles/{article['id']}")

@pytest.mark.parametrize(
    "payload, field",
    [
    ({"body": "No title"}, "title"),
    ({"title": "ab", "body": "Too short"}, "title"),
    ({"title": "x" * 121, "body": "Too long"}, "title"),
    ({"title": "Valid title", "body": " "}, "body"),
    ({"title": "Valid title", "body": "Bad status", "status": "archived"}, "status"),
    ],
    ids=["missing-title", "title-2-chars", "title-121-chars", "blank-body", "bad-status"],
)

def test_create_rejects_invalid_payload(editor_api, payload, field):
    """API-TC-021: invalid payloads return 400 with the failing field named."""
    response = editor_api.post("/api/articles", json=payload)
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "validation_failed"
    assert field in body["fields"]

@pytest.mark.parametrize("length", [3, 120], ids=["min-3", "max-120"])
def test_create_accepts_boundary_title_lengths(editor_api, length):
    """API-TC-022: titles of exactly 3 and 120 characters are accepted."""
    response = editor_api.post(
    "/api/articles", json={"title": "T" * length, "body": "Boundary value."}
    )
    assert response.status_code == 201, response.text
    editor_api.delete(f"/api/articles/{response.json()['id']}")
# ---------------------------------------------------------------- update / delete / search
def test_update_article_title(editor_api, created_article):
    """API-TC-023: PUT changes the title and the change is persisted."""
    new_title = created_article["title"] + " (edited)"
    response = editor_api.put(f"/api/articles/{created_article['id']}", json={"title": new_title})
    assert response.status_code == 200
    assert editor_api.get(f"/api/articles/{created_article['id']}").json()["title"] == new_title

def test_delete_article(editor_api, unique_title):
    """API-TC-024: DELETE returns 204 and the article is gone."""
    article_id = editor_api.post(
    "/api/articles", json={"title": unique_title, "body": "To delete."}
    ).json()["id"]
    response = editor_api.delete(f"/api/articles/{article_id}")
    assert response.status_code == 204
    assert editor_api.get(f"/api/articles/{article_id}").status_code == 404

def test_search_finds_article_by_title(anon_api, created_article):
    """API-TC-025: ?q= matches part of the title."""
    term = created_article["title"].split()[-1]
    response = anon_api.get("/api/articles", params={"q": term})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [created_article["id"]]
