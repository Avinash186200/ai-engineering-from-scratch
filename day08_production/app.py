"""FastAPI service for the research assistant chatbot.

POST /chat          run the Day 3 agent through the resilient LLM adapter
POST /chat/stream   the same answer as Server-Sent Events
GET  /healthz       liveness: is the process alive?
GET  /readyz        readiness: can it serve traffic right now?

Run (from the repo root):  uvicorn day08_production.app:app --port 8000   then open /docs
Self-test, no server:      python day08_production/app.py --selftest
Config comes from the environment:
  LLM_PROVIDERS=fake        comma-separated failover order, e.g. claude,fake
  LOG_LEVEL=INFO
  ANTHROPIC_API_KEY=...     only for the claude provider; never printed
"""
import asyncio
import logging
import os
import re
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

HERE = Path(__file__).resolve().parent
for p in (HERE.parent, HERE.parent / "day03_agents", HERE):
    sys.path.insert(0, str(p))
from agent import ask, build_app  # noqa: E402
from core.fund_model import rank_funds  # noqa: E402
from llm_adapter import LLMUnavailable, default_llm  # noqa: E402

PROVIDERS = os.environ.get("LLM_PROVIDERS", "fake").split(",")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
API_KEY = os.environ.get("ANTHROPIC_API_KEY")   # never printed

# run it:
# docker run --env-file prod.env -p 8000:8000 chatbot

logging.basicConfig(level=LOG_LEVEL)
log = logging.getLogger("chatbot")


class Agent:
    """The Day 3 graph behind an async interface. Built once, at start-up."""

    def __init__(self, providers):
        self.graph = build_app(default_llm(providers))

    async def answer(self, thread_id: str, message: str) -> str:
        out = await asyncio.to_thread(ask, self.graph, message, thread_id)
        return out["answer"]

    async def stream(self, thread_id: str, message: str):
        text = await self.answer(thread_id, message)
        for word in text.split(" "):           # a fake model has no token stream: send words
            yield word + " "


def build_agent(providers=None) -> Agent:
    return Agent(providers or PROVIDERS)


def format_table(table: dict) -> str:
    if "error" in table:
        return f"Ranking unavailable: {table['error']}"
    rows = [f"{r['rank']}. {r['fund']}  {r['predicted_return']:+.2%}  NAV {r['nav']}"
            for r in table["top"]]
    return f"Ranking for {table['as_of']}:\n" + "\n".join(rows) + f"\n{table['caveat']}"


app = FastAPI(title="Research assistant chatbot")
agent = build_agent()          # built once, at start-up


class ChatRequest(BaseModel):
    thread_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    thread_id: str
    answer: str


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready", "providers": PROVIDERS}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    try:
        answer = await agent.answer(req.thread_id, req.message)
    except LLMUnavailable:
        m = re.search(r"\d{4}-\d{2}-\d{2}", req.message)
        parsed_date = m.group(0) if m else ""
        table = rank_funds(as_of=parsed_date, top_n=5)   # the tool still works
        answer = format_table(table) + (
            "\n\nThe language model is temporarily unavailable; "
            "this is the raw ranking without commentary.")
        log.warning("LLM unavailable; served the raw ranking")
    return ChatResponse(thread_id=req.thread_id, answer=answer)


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def events():
        yield "event: status\ndata: ranking funds...\n\n"
        async for token in agent.stream(req.thread_id, req.message):
            yield f"event: token\ndata: {token}\n\n"
        yield "event: done\ndata: \n\n"
    return StreamingResponse(events(), media_type="text/event-stream")


if __name__ == "__main__" and "--selftest" in sys.argv:
    from fastapi.testclient import TestClient
    c = TestClient(app)
    print("GET /healthz ->", c.get("/healthz").json())
    print("GET /readyz  ->", c.get("/readyz").json())
    for msg in ["Which funds look best on 2025-06-19?", "What is a SIP?", ""]:
        r = c.post("/chat", json={"thread_id": "priya-1", "message": msg})
        body = r.json() if r.status_code == 200 else "rejected by validation"
        print(f"POST /chat {msg!r} -> {r.status_code} {body}")
    r = c.post("/chat/stream", json={"thread_id": "priya-2", "message": "What is NAV?"})
    print("POST /chat/stream ->", r.status_code, r.text.splitlines()[:4])
    agent = build_agent(["down"])                  # every provider down: graceful fallback
    r = c.post("/chat", json={"thread_id": "priya-3", "message": "Which funds look best on 2025-06-19?"})
    print("POST /chat with the LLM down ->", r.status_code, r.json()["answer"])
