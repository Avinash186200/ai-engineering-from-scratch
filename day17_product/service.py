"""One model, many consumers: a versioned REST API in front of the same function the agent's MCP tool uses.

Who calls the model:
  - the AI agent       -> the MCP tool (day04_mcp/fund_mcp_server.py)
  - Excel users        -> this REST API: JSON via Power Query, or CSV (excel_power_query.m)
  - notebooks/scripts  -> this REST API via a small client (client.py)
  - other services     -> this REST API, documented by OpenAPI at /docs

Product rules this file demonstrates:
  1. ONE implementation (core.fund_model.rank_funds). Every channel calls it, so answers never disagree.
  2. Versioned contract: /v1 never changes shape. Improvements go to /v2. Old clients keep working.
  3. Units in the contract: v2 says 'predicted_return_pct', not an ambiguous 'return'.
  4. Every response says what produced it: model, model version, as-of date used.
  5. API keys per client, so usage can be counted, limited and revoked per client.
  6. Errors are typed and documented, never stack traces.
  7. Deprecation is announced in headers before anything is removed.

Run:  python day17_product/service.py          (self-test, no server)
Serve: uvicorn day17_product.service:app --port 8010   then open http://localhost:8010/docs
"""
from __future__ import annotations

import csv
import io
import os
import sys
from collections import Counter
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.fund_model import rank_funds

MODEL_VERSION = os.environ.get("MODEL_VERSION", "quantile-2025.06")
API_KEYS = {"demo-key-excel-team": "excel-team", "demo-key-research-nb": "research-notebooks"}   # in production: hashed, in a DB
USAGE: Counter = Counter()


def client_name(x_api_key: str = Header(default="")) -> str:
    name = API_KEYS.get(x_api_key)
    if name is None:
        raise HTTPException(401, {"code": "UNAUTHENTICATED", "message": "send a valid X-API-Key header"})
    USAGE[name] += 1
    return name


class RowV1(BaseModel):
    rank: int
    fund: str
    predicted_return: float          # decimal: 0.0099 = 0.99%  (v1 contract, frozen)
    nav: float


class RankingV1(BaseModel):
    as_of: str
    top: list[RowV1]


class RowV2(BaseModel):
    rank: int
    fund: str
    predicted_return_pct: float      # explicit unit
    nav: float


class RankingV2(BaseModel):
    as_of_used: str
    model: str
    model_version: str
    n_scored: int
    excluded_count: int
    caveat: str
    top: list[RowV2]


def _ranking(as_of: str, top_n: int) -> dict:
    out = rank_funds(as_of, top_n=top_n)
    if "error" in out:
        raise HTTPException(422, {"code": "INVALID_ARGUMENT", "message": out["error"]})
    return out


app = FastAPI(title="Fund ranking model API", version="2.0",
              description="The same ranking model the research assistant uses, for Excel, notebooks and services.")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_version": MODEL_VERSION}


@app.get("/v1/rank", response_model=RankingV1, deprecated=True)
def rank_v1(as_of: str = "", top_n: int = Query(5, ge=1, le=20), client: str = Depends(client_name)):
    out = _ranking(as_of, top_n)
    return {"as_of": out["as_of"], "top": out["top"]}


@app.get("/v2/rank", response_model=RankingV2)
def rank_v2(as_of: str = "", top_n: int = Query(5, ge=1, le=20), client: str = Depends(client_name)):
    out = _ranking(as_of, top_n)
    return {"as_of_used": out["as_of"], "model": out["model"], "model_version": MODEL_VERSION,
            "n_scored": out["n_scored"], "excluded_count": len(out["excluded"]), "caveat": out["caveat"],
            "top": [{"rank": r["rank"], "fund": r["fund"], "predicted_return_pct": round(r["predicted_return"] * 100, 2),
                     "nav": r["nav"]} for r in out["top"]]}


@app.get("/v2/rank.csv", response_class=PlainTextResponse)
def rank_v2_csv(as_of: str = "", top_n: int = Query(5, ge=1, le=20), client: str = Depends(client_name)):
    """Flat CSV for spreadsheets: Excel can load this with Data > From Web, or Power Query."""
    data = rank_v2(as_of, top_n, client)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["as_of_used", "rank", "fund", "predicted_return_pct", "nav", "model_version"])
    for r in data["top"]:
        w.writerow([data["as_of_used"], r["rank"], r["fund"], r["predicted_return_pct"], r["nav"], data["model_version"]])
    return buf.getvalue()


@app.middleware("http")
async def deprecation_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/v1/"):
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = "Wed, 31 Dec 2026 23:59:59 GMT"
        response.headers["Link"] = '</v2/rank>; rel="successor-version"'
    return response


def _selftest() -> None:
    from fastapi.testclient import TestClient

    c = TestClient(app)
    key = {"X-API-Key": "demo-key-excel-team"}
    v1 = c.get("/v1/rank", params={"as_of": "2025-06-19", "top_n": 3}, headers=key)
    v2 = c.get("/v2/rank", params={"as_of": "2025-06-19", "top_n": 3}, headers=key)
    csv_r = c.get("/v2/rank.csv", params={"as_of": "2025-06-19", "top_n": 3}, headers=key)
    print("v1 :", v1.status_code, v1.json()["top"][0], "| Deprecation:", v1.headers.get("Deprecation"))
    print("v2 :", v2.status_code, v2.json()["top"][0], "| model", v2.json()["model_version"])
    print("csv:", csv_r.text.splitlines()[:2])
    print("no key  ->", c.get("/v2/rank", params={"as_of": "2025-06-19"}).status_code)
    print("weekend ->", c.get("/v2/rank", params={"as_of": "2025-06-21"}, headers=key).json()["detail"])

    assert v1.status_code == v2.status_code == 200
    assert set(v1.json()) == {"as_of", "top"} and set(v1.json()["top"][0]) == {"rank", "fund", "predicted_return", "nav"}
    assert abs(v1.json()["top"][0]["predicted_return"] * 100 - v2.json()["top"][0]["predicted_return_pct"]) < 0.01
    assert v1.json()["top"][0]["fund"] == v2.json()["top"][0]["fund"]          # same model, same answer
    assert c.get("/v2/rank").status_code == 401
    assert "/v1/rank" in c.get("/openapi.json").json()["paths"]
    print("usage per client:", dict(USAGE))
    print("ok: v1 contract frozen, v2 explicit units, CSV for Excel, keys per client, typed errors")


if __name__ == "__main__":
    _selftest()
