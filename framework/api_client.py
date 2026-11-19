"""Thin wrapper around requests.Session so tests read like the API contract."""
import requests

from framework.config import REQUEST_TIMEOUT


class ApiClient:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _url(self, path):
        return f"{self.base_url}{path}"

    def get(self, path, **kwargs):
        return self.session.get(self._url(path), timeout=REQUEST_TIMEOUT, **kwargs)

    def post(self, path, **kwargs):
        return self.session.post(self._url(path), timeout=REQUEST_TIMEOUT, **kwargs)

    def put(self, path, **kwargs):
        return self.session.put(self._url(path), timeout=REQUEST_TIMEOUT, **kwargs)

    def delete(self, path, **kwargs):
        return self.session.delete(self._url(path), timeout=REQUEST_TIMEOUT, **kwargs)


def get_token(base_url, credentials):
    response = requests.post(
        f"{base_url}/api/auth/token", json=credentials, timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()["token"]
