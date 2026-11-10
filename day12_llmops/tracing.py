"""Tracing for LLM apps: one trace per request, one span per step, written as JSON lines.

What gets recorded for every LLM or tool call:
  trace_id, span name, start time, latency_ms, status (ok / error), model,
  input and output tokens, cost in USD, and the (redacted) prompt and answer.

Why JSON lines: one record per line is easy to append, grep, and load into pandas,
and every real tool (OpenTelemetry, Langfuse, LangSmith, Datadog) accepts the same fields.

Run:  python day12_llmops/tracing.py
"""
from __future__ import annotations

import json
import re
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

# Illustrative prices in USD per million tokens. Real prices change: keep them in config, not code.
PRICES = {
    "large-model": {"in": 15.00, "out": 75.00},
    "small-model": {"in": 0.80, "out": 4.00},
    "fake": {"in": 0.0, "out": 0.0},
}

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"(?<!\d)(?:\+91[- ]?)?[6-9]\d{9}(?!\d)")
PAN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")          # Indian tax ID format
KEY = re.compile(r"\b(?:sk|pk|api)[-_][A-Za-z0-9_-]{8,}\b")


def redact(text: str) -> str:
    """Remove personal data and secrets BEFORE anything is written to a log."""
    text = EMAIL.sub("[EMAIL]", text)
    text = PHONE.sub("[PHONE]", text)
    text = PAN.sub("[PAN]", text)
    return KEY.sub("[SECRET]", text)


def estimate_tokens(text: str) -> int:
    """Rough count (about 4 characters per token in English). Use the provider's count when you have it."""
    return max(1, len(text) // 4)


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    p = PRICES.get(model, PRICES["large-model"])          # unknown model: assume the expensive one
    return round((tokens_in * p["in"] + tokens_out * p["out"]) / 1_000_000, 6)


class Tracer:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.trace_id = ""

    def new_trace(self, user: str = "anon") -> str:
        self.trace_id = uuid.uuid4().hex[:12]
        self.user = user
        return self.trace_id

    def write(self, record: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    @contextmanager
    def span(self, name: str, **fields):
        """Times a step and always writes a record, even when the step raises."""
        rec = {"trace_id": self.trace_id, "user": getattr(self, "user", "anon"), "span": name,
               "ts": time.time(), "status": "ok", **fields}
        t0 = time.perf_counter()
        try:
            yield rec                      # the step fills in tokens, answer, etc.
        except Exception as e:
            rec["status"] = "error"
            rec["error"] = f"{type(e).__name__}: {e}"[:200]
            raise
        finally:
            rec["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            for k in ("prompt", "answer"):
                if k in rec:
                    rec[k] = redact(str(rec[k]))[:500]
            self.write(rec)

    def llm_call(self, model: str, prompt: str, call):
        """Wraps any LLM function: call(prompt) -> answer text. Records tokens and cost."""
        with self.span("llm", model=model, prompt=prompt) as rec:
            answer = call(prompt)
            rec["tokens_in"] = estimate_tokens(prompt)
            rec["tokens_out"] = estimate_tokens(answer)
            rec["cost_usd"] = cost_usd(model, rec["tokens_in"], rec["tokens_out"])
            rec["answer"] = answer
            return answer


def load(path: str | Path) -> list[dict]:
    p = Path(path)
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()] if p.exists() else []


if __name__ == "__main__":
    out = Path(__file__).parent / "out" / "demo_traces.jsonl"
    out.unlink(missing_ok=True)
    t = Tracer(out)
    t.new_trace(user="priya")
    with t.span("tool", tool="rank_funds") as r:
        r["result_rows"] = 5
    t.llm_call("small-model", "Top funds on 2025-06-20? Mail me at priya@example.com",
               lambda p: "Fund A leads with a predicted +0.99% over 20 days.")
    try:
        with t.span("tool", tool="fund_info"):
            raise TimeoutError("upstream took 30s")
    except TimeoutError:
        pass
    for rec in load(out):
        print(json.dumps(rec))
    assert "[EMAIL]" in out.read_text() and "priya@example.com" not in out.read_text()
    print("ok: 3 spans written, email redacted, error span recorded")
