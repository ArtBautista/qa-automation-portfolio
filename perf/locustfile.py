"""Locust load model for the Content Portal.

Run (headless):
  locust -f perf/locustfile.py --headless -u 20 -r 5 -t 1m --host http://127.0.0.1:5000 \
      --csv reports/perf --html reports/perf-report.html --exit-code-on-error 0
"""
import os
import random
import uuid
from locust import HttpUser, between, task

EDITOR = {
    "username": os.environ.get("EDITOR_USER", "editor"),
    "password": os.environ.get("EDITOR_PASS", "Editor#2026"),
}
SEARCH_TERMS = ["exam", "welcome", "portal", "tips", "qa"]
class ReaderUser(HttpUser):
    """Anonymous visitor: 80% of traffic. Browses, reads and searches."""

    weight = 4
    wait_time = between(1, 3)

    def on_start(self):
        response = self.client.get("/api/articles?limit=50", name="GET /api/articles (warm-up)")
        items = response.json().get("items", []) if response.ok else []
        self.article_ids = [item["id"] for item in items] or [1]

    @task(5)
    def home_page(self):
        self.client.get("/", name="GET /")

    @task(4)
    def list_articles(self):
        with self.client.get(
            "/api/articles?limit=20", name="GET /api/articles", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status {response.status_code}")
            elif "items" not in response.json():
                response.failure("Response has no 'items' key")
            else:
                response.success()
    @task(3)
    def read_article(self):
        article_id = random.choice(self.article_ids)
        self.client.get(f"/articles/{article_id}", name="GET /articles/[id]")

    @task(2)
    def search(self):
        term = random.choice(SEARCH_TERMS)
        self.client.get(f"/search?q={term}", name="GET /search")

    @task(1)
    def popular_report(self):
        self.client.get("/api/reports/popular", name="GET /api/reports/popular")

class EditorUser(HttpUser):
    """Signed-in editor: 20% of traffic. Creates, lists and deletes content."""
    weight = 1
    wait_time = between(2, 5)

    def on_start(self):
        response = self.client.post("/api/auth/token", json=EDITOR, name="POST /api/auth/token")
        token = response.json().get("token", "") if response.ok else ""
        self.headers = {"Authorization": f"Bearer {token}"}

    @task(2)
    def list_all_articles(self):
        self.client.get(
            "/api/articles?status=all&limit=50",
            headers=self.headers,
            name="GET /api/articles?status=all",
            )
    @task(1)
    def create_and_delete_article(self):
        payload = {
            "title": f"Load test {uuid.uuid4().hex[:8]}",
            "body": "Created by Locust.",
            "status": "draft",
        }
        with self.client.post(
            "/api/articles",
            json=payload,
            headers=self.headers,
            name="POST /api/articles",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(f"Create failed: {response.status_code}")
                return
            response.success()
            article_id = response.json()["id"]
        self.client.delete(
            f"/api/articles/{article_id}", headers=self.headers, name="DELETE /api/articles/[id]"
        )
