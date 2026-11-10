"""Layer 3: API contract tests. The HTTP surface is a promise to clients: status codes, schemas, errors.

FastAPI's TestClient calls the app in-process: no server, no network, fast.
In CI you can add schemathesis, which reads the OpenAPI schema and fuzzes every endpoint:
    schemathesis run http://localhost:8000/openapi.json --checks all
"""
from __future__ import annotations


def test_health_and_ready(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json()["status"] == "ready"


def test_chat_returns_the_documented_shape(client, a_business_day):
    r = client.post("/chat", json={"thread_id": "t-1", "message": f"Which funds look best on {a_business_day}?"})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"thread_id", "answer"} and body["thread_id"] == "t-1"
    assert body["answer"].strip()


def test_validation_rejects_bad_requests(client):
    assert client.post("/chat", json={"thread_id": "t", "message": ""}).status_code == 422
    assert client.post("/chat", json={"thread_id": "", "message": "hi"}).status_code == 422
    assert client.post("/chat", json={"thread_id": "t", "message": "x" * 4001}).status_code == 422
    assert client.post("/chat", json={"message": "no thread"}).status_code == 422


def test_openapi_schema_lists_the_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/chat", "/chat/stream", "/healthz", "/readyz"} <= set(paths)


def test_stream_uses_server_sent_events(client):
    r = client.post("/chat/stream", json={"thread_id": "t-2", "message": "What is NAV?"})
    assert r.headers["content-type"].startswith("text/event-stream")
    events = [line for line in r.text.splitlines() if line.startswith("event:")]
    assert events[0] == "event: status" and events[-1] == "event: done"
    assert "event: token" in events


def test_llm_outage_degrades_gracefully(chat_app, client, a_business_day):
    original = chat_app.agent
    chat_app.agent = chat_app.build_agent(["down"])        # every provider fails
    try:
        r = client.post("/chat", json={"thread_id": "t-3", "message": f"Which funds look best on {a_business_day}?"})
    finally:
        chat_app.agent = original
    assert r.status_code == 200
    assert "temporarily unavailable" in r.json()["answer"]
    assert f"Ranking for {a_business_day}" in r.json()["answer"]
