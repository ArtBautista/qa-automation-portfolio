"""Central test configuration. Every value can be overridden with an environment variable."""
import os

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000").rstrip("/")
EDITOR = {
    "username": os.environ.get("EDITOR_USER", "editor"),
    "password": os.environ.get("EDITOR_PASS", "Editor#2026"),
}
VIEWER = {
    "username": os.environ.get("VIEWER_USER", "viewer"),
    "password": os.environ.get("VIEWER_PASS", "Viewer#2026"),
}
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "10"))
