"""Generate 7 days of fake production traffic, with three incidents hidden in it.

  Day 5: the LLM provider gets slow           -> latency p95 jumps, some timeouts
  Day 6: someone ships a new prompt           -> the model starts inventing numbers (groundedness drops)
  Day 7: users start asking about a new topic -> question drift (topics the tools don't cover)

The monitor (monitor.py) must find all three from the traces alone.
Seeded, so every run prints the same numbers.

Run:  python day12_llmops/simulate.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from day12_llmops.guards import run_all
from day12_llmops.tracing import cost_usd, redact

OUT = Path(__file__).parent / "out" / "traces.jsonl"
TOPICS = {"ranking": 0.55, "definition": 0.30, "fund_info": 0.15}
DRIFT_TOPICS = {"ranking": 0.35, "definition": 0.20, "fund_info": 0.10, "crypto": 0.35}
FUNDS = ["Fund Alpha", "Fund Beta", "Fund Gamma", "Fund Delta"]


def one_request(rng: random.Random, day: int, i: int) -> dict:
    topics = DRIFT_TOPICS if day == 7 else TOPICS
    topic = rng.choices(list(topics), weights=list(topics.values()))[0]
    model = "small-model" if topic == "definition" else "large-model"     # routing: cheap model for easy asks
    evidence = [{"fund": f, "predicted_return": round(rng.uniform(0.002, 0.012), 4)} for f in rng.sample(FUNDS, 2)]
    top = max(evidence, key=lambda e: e["predicted_return"])
    pct = round(top["predicted_return"] * 100, 2)

    latency = rng.lognormvariate(7.0, 0.35)                  # about 1.1 s median
    status = "ok"
    if day == 5:
        latency *= rng.uniform(2.5, 4.0)
        if rng.random() < 0.06:
            status, latency = "error", 30000.0              # timeout

    if topic == "crypto":
        answer = "I can't help with crypto prices; I only cover mutual funds."
    elif day == 6 and rng.random() < 0.30:                  # new prompt: "be confident and specific"
        answer = f"{top['fund']} will deliver about {round(pct * rng.uniform(1.8, 3.0), 1)}% next month."
    else:
        answer = f"{top['fund']} ranks first with a predicted {pct}% over 20 trading days."

    question = {"ranking": "Which funds look best on 2025-06-20?", "definition": "What is an exit load?",
                "fund_info": "Tell me about Fund Beta", "crypto": "Should I buy bitcoin? call me 9876543210"}[topic]
    t_in, t_out = rng.randint(900, 1600), rng.randint(60, 180)
    checks = run_all(answer, evidence) if status == "ok" else {"pass": None, "checks": []}
    return {"trace_id": f"d{day}-{i:04d}", "day": day, "span": "llm", "topic": topic, "model": model,
            "status": status, "latency_ms": round(latency, 1), "tokens_in": t_in, "tokens_out": t_out,
            "cost_usd": cost_usd(model, t_in, t_out), "prompt": redact(question),
            "answer": answer if status == "ok" else "", "guard_pass": checks["pass"],
            "guard_failed": [c["check"] for c in checks["checks"] if not c["pass"]],
            "thumb": (rng.random() < (0.55 if checks["pass"] is False else 0.08)) and "down" or None}


def generate(path: Path = OUT, days: int = 7, per_day: int = 300, seed: int = 12) -> Path:
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for day in range(1, days + 1):
            for i in range(per_day):
                f.write(json.dumps(one_request(rng, day, i)) + "\n")
    return path


if __name__ == "__main__":
    p = generate()
    n = sum(1 for _ in p.open(encoding="utf-8"))
    print(f"wrote {n} traces to {p}")
