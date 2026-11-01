"""FastAPI service: POST /chat runs the day03 agent through the resilient adapter; GET /health.

Run:  uvicorn app:app --app-dir day08_production --port 8000
Then: curl -X POST localhost:8000/chat -H "content-type: application/json"
           -d '{"message": "top 3 funds on 2024-11-04", "session_id": "u1"}'
Self-test without a server:  python day08_production/app.py --selftest
Set USE_REAL_LLM=1 to use Claude as the primary provider.
"""
import os
import sys
import time
import uuid
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

HERE = Path(__file__).resolve().parent
for p in (HERE.parent, HERE.parent / "day03_agents", HERE):
    sys.path.insert(0, str(p))
from agent import build_graph  # noqa: E402
from llm_adapter import default_llm  # noqa: E402

app = FastAPI(title="Fund Research Assistant")
graph = build_graph(default_llm(real=os.getenv("USE_REAL_LLM") == "1"))


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(default="anon", max_length=64)


class ChatOut(BaseModel):
    answer: str
    tools_used: list[str]
    request_id: str
    latency_ms: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    t0, rid = time.perf_counter(), uuid.uuid4().hex[:8]
    cfg = {"configurable": {"thread_id": body.session_id}}
    before = len(graph.get_state(cfg).values.get("messages", []))
    state = graph.invoke({"messages": [{"role": "user", "content": body.message}], "steps": 0}, cfg)
    new = state["messages"][before:]
    tools = [c["name"] for m in new if m["role"] == "assistant" for c in m.get("tool_calls", [])]
    return ChatOut(answer=state["messages"][-1]["content"], tools_used=tools, request_id=rid,
                   latency_ms=int((time.perf_counter() - t0) * 1000))


if __name__ == "__main__" and "--selftest" in sys.argv:
    from fastapi.testclient import TestClient
    c = TestClient(app)
    print("GET /health ->", c.get("/health").json())
    for msg in ["top 3 funds on 2024-11-04", "What is SIP?", ""]:
        r = c.post("/chat", json={"message": msg, "session_id": "selftest"})
        body = r.json() if r.status_code == 200 else "validation error"
        print(f"POST /chat {msg!r} -> {r.status_code} {body}")
