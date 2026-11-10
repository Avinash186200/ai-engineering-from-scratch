"""A tiny Python client for the model API, for notebooks and scripts.

Why ship a client at all: users shouldn't have to know headers, retries or error formats.
  - one place for the base URL and API key (from an environment variable, never in the notebook)
  - timeouts and retries with backoff for transient errors (429, 5xx), never for 4xx mistakes
  - typed errors: ModelAPIError has the API's error code and message
  - returns plain Python (or a pandas DataFrame if pandas is installed)

Usage in a notebook:
    from day17_product.client import ModelClient
    c = ModelClient("https://models.example.com")         # key from MODEL_API_KEY
    c.rank("2025-06-19", top_n=5)                         # dict
    c.rank_df("2025-06-19")                               # pandas DataFrame

Run:  python day17_product/client.py      (self-test against the in-process app, no server)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RETRYABLE = {429, 500, 502, 503, 504}


class ModelAPIError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(f"{status} {code}: {message}")
        self.status, self.code, self.message = status, code, message


def urllib_transport(method: str, url: str, headers: dict, timeout: float):
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "null")


class ModelClient:
    def __init__(self, base_url: str, api_key: str | None = None, timeout: float = 30.0,
                 retries: int = 3, transport=urllib_transport, sleep=time.sleep):
        self.base = base_url.rstrip("/")
        self.key = api_key or os.environ.get("MODEL_API_KEY", "")
        self.timeout, self.retries, self.transport, self.sleep = timeout, retries, transport, sleep

    def _get(self, path: str, **params) -> dict:
        url = f"{self.base}{path}?{urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})}"
        for attempt in range(self.retries + 1):
            status, body = self.transport("GET", url, {"X-API-Key": self.key}, self.timeout)
            if status == 200:
                return body
            if status in RETRYABLE and attempt < self.retries:
                self.sleep(min(2 ** attempt, 10))                      # 1, 2, 4 ... seconds
                continue
            detail = (body or {}).get("detail", {}) if isinstance(body, dict) else {}
            if isinstance(detail, dict):
                raise ModelAPIError(status, detail.get("code", "ERROR"), detail.get("message", str(body)))
            raise ModelAPIError(status, "ERROR", str(detail))
        raise ModelAPIError(503, "UNAVAILABLE", "retries exhausted")

    def rank(self, as_of: str = "", top_n: int = 5) -> dict:
        return self._get("/v2/rank", as_of=as_of, top_n=top_n)

    def rank_df(self, as_of: str = "", top_n: int = 5):
        import pandas as pd
        data = self.rank(as_of, top_n)
        return pd.DataFrame(data["top"]).assign(as_of_used=data["as_of_used"], model_version=data["model_version"])


def _selftest() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from fastapi.testclient import TestClient
    from day17_product.service import app

    tc = TestClient(app)
    flaky = {"left": 2}

    def transport(method, url, headers, timeout):
        if flaky["left"] > 0:                          # the first two calls hit a 'busy' server
            flaky["left"] -= 1
            return 503, {"detail": "busy"}
        r = tc.get(url.replace("http://test", ""), headers=headers)
        return r.status_code, r.json()

    waits = []
    c = ModelClient("http://test", api_key="demo-key-research-nb", transport=transport, sleep=waits.append)
    data = c.rank("2025-06-19", top_n=3)
    print("after 2 retries:", data["top"][0]["fund"], data["top"][0]["predicted_return_pct"], "| waited", waits)
    try:
        c.rank("2025-06-21")
    except ModelAPIError as e:
        print("typed error    :", e.status, e.code)
        assert e.code == "INVALID_ARGUMENT" and len(waits) == 2       # no retry on a 4xx
    try:
        ModelClient("http://test", api_key="wrong", transport=transport, sleep=waits.append).rank("2025-06-19")
    except ModelAPIError as e:
        print("bad key        :", e.status, e.code)
        assert e.status == 401
    print("ok: retries on 503 with backoff, no retry on 422/401, typed errors")


if __name__ == "__main__":
    _selftest()
