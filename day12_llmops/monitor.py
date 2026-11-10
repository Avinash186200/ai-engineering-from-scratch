"""Turn traces into a daily dashboard and alerts.

Golden signals for an LLM app (per day):
  volume, error rate, latency p50 / p95, cost per request, total cost,
  guard pass rate (groundedness), refusal rate, thumbs-down rate, topic drift (PSI).

Two kinds of alert:
  - fixed thresholds (SLOs): p95 latency > 3000 ms, error rate > 2%, guard pass < 95%
  - change vs baseline: today vs the first days (drift, cost jumps)

Run:  python day12_llmops/monitor.py          (generates traffic first if needed)
      python day12_llmops/monitor.py --selftest
"""
from __future__ import annotations

import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from day12_llmops.simulate import OUT, generate
from day12_llmops.tracing import load

SLO = {"p95_ms": 3000, "error_rate": 0.02, "guard_pass": 0.95, "psi": 0.2, "cost_jump": 1.5}


def pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    v = sorted(values)
    return v[min(len(v) - 1, int(math.ceil(q * len(v))) - 1)]


def psi(base: Counter, now: Counter) -> float:
    """Population Stability Index: 0 = same mix, > 0.2 = the mix has really changed."""
    keys = set(base) | set(now)
    b_tot, n_tot = sum(base.values()), sum(now.values())
    total = 0.0
    for k in keys:
        b = max(base[k] / b_tot, 1e-4)
        n = max(now[k] / n_tot, 1e-4)
        total += (n - b) * math.log(n / b)
    return round(total, 3)


def daily(traces: list[dict]) -> list[dict]:
    by_day = defaultdict(list)
    for t in traces:
        by_day[t["day"]].append(t)
    base_topics = Counter(t["topic"] for d in (1, 2, 3) for t in by_day[d])
    rows = []
    for day in sorted(by_day):
        ts = by_day[day]
        ok = [t for t in ts if t["status"] == "ok"]
        lat = [t["latency_ms"] for t in ok]
        rows.append({
            "day": day, "n": len(ts),
            "error_rate": round(1 - len(ok) / len(ts), 3),
            "p50_ms": round(pct(lat, 0.5)), "p95_ms": round(pct(lat, 0.95)),
            "cost_per_req": round(sum(t["cost_usd"] for t in ts) / len(ts), 4),
            "cost_total": round(sum(t["cost_usd"] for t in ts), 2),
            "guard_pass": round(sum(1 for t in ok if t["guard_pass"]) / max(1, len(ok)), 3),
            "refusal": round(sum(1 for t in ok if "is_refusal" in t["guard_failed"]) / max(1, len(ok)), 3),
            "thumbs_down": round(sum(1 for t in ts if t.get("thumb") == "down") / len(ts), 3),
            "psi": psi(base_topics, Counter(t["topic"] for t in ts)),
        })
    return rows


def alerts(rows: list[dict]) -> list[str]:
    base_cost = sum(r["cost_per_req"] for r in rows[:3]) / 3
    out = []
    for r in rows:
        d = f"day {r['day']}"
        if r["p95_ms"] > SLO["p95_ms"]:
            out.append(f"{d}: LATENCY p95 {r['p95_ms']} ms > {SLO['p95_ms']} ms")
        if r["error_rate"] > SLO["error_rate"]:
            out.append(f"{d}: ERRORS {r['error_rate']:.1%} > {SLO['error_rate']:.0%}")
        if r["guard_pass"] < SLO["guard_pass"]:
            out.append(f"{d}: GROUNDEDNESS guard pass {r['guard_pass']:.1%} < {SLO['guard_pass']:.0%}")
        if r["psi"] > SLO["psi"]:
            out.append(f"{d}: DRIFT topic PSI {r['psi']} > {SLO['psi']}")
        if r["cost_per_req"] > SLO["cost_jump"] * base_cost:
            out.append(f"{d}: COST per request {r['cost_per_req']} > {SLO['cost_jump']}x baseline")
    return out


def show(rows: list[dict]) -> None:
    cols = ["day", "n", "error_rate", "p50_ms", "p95_ms", "cost_per_req", "cost_total",
            "guard_pass", "refusal", "thumbs_down", "psi"]
    print(" ".join(f"{c:>12}" for c in cols))
    for r in rows:
        print(" ".join(f"{r[c]:>12}" for c in cols))


def main(selftest: bool = False) -> None:
    if selftest or not OUT.exists():
        generate()
    rows = daily(load(OUT))
    show(rows)
    found = alerts(rows)
    print("\nALERTS")
    for a in found or ["none"]:
        print(" -", a)
    if selftest:
        text = "\n".join(found)
        assert "day 5: LATENCY" in text and "day 5: ERRORS" in text, "missed the slow provider"
        assert "day 6: GROUNDEDNESS" in text, "missed the bad prompt"
        assert "day 7: DRIFT" in text, "missed the topic drift"
        assert not any(a.startswith(("day 1:", "day 2:", "day 3:", "day 4:")) for a in found), "false alarm"
        print("\nselftest ok: all 3 incidents caught, no false alarms on days 1-4")


if __name__ == "__main__":
    main(selftest="--selftest" in sys.argv)
