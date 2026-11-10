"""Canary decision: send a small share of traffic to the new version, compare, then promote or roll back.

The rule is written down BEFORE the rollout, so nobody argues with the numbers afterwards:
  - enough traffic on the canary to judge (minimum requests)
  - error rate not worse than baseline by more than an allowed margin
  - p95 latency not worse than baseline by more than X%
  - quality (answer-check pass rate, Day 12) not lower than baseline by more than a margin

Run:  python day13_cloud/canary.py
"""
from __future__ import annotations

import random
from dataclasses import dataclass

RULES = {"min_requests": 200, "max_error_increase": 0.01, "max_p95_increase": 0.20, "max_quality_drop": 0.02}


@dataclass
class Stats:
    requests: int
    errors: int
    p95_ms: float
    quality: float          # share of answers passing automatic checks

    @property
    def error_rate(self) -> float:
        return self.errors / max(1, self.requests)


def decide(base: Stats, canary: Stats, rules: dict = RULES) -> tuple[str, list[str]]:
    """Returns ('wait' | 'promote' | 'rollback', reasons)."""
    if canary.requests < rules["min_requests"]:
        return "wait", [f"only {canary.requests} canary requests, need {rules['min_requests']}"]
    reasons = []
    if canary.error_rate > base.error_rate + rules["max_error_increase"]:
        reasons.append(f"error rate {canary.error_rate:.1%} vs {base.error_rate:.1%}")
    if canary.p95_ms > base.p95_ms * (1 + rules["max_p95_increase"]):
        reasons.append(f"p95 {canary.p95_ms:.0f} ms vs {base.p95_ms:.0f} ms")
    if canary.quality < base.quality - rules["max_quality_drop"]:
        reasons.append(f"quality {canary.quality:.1%} vs {base.quality:.1%}")
    return ("rollback", reasons) if reasons else ("promote", ["all checks within limits"])


def simulate(n: int, err: float, lat: float, qual: float, rng: random.Random) -> Stats:
    lats = sorted(rng.lognormvariate(lat, 0.35) for _ in range(n))
    return Stats(n, sum(rng.random() < err for _ in range(n)), lats[int(0.95 * n) - 1] if n else 0.0,
                 sum(rng.random() < qual for _ in range(n)) / max(1, n))


if __name__ == "__main__":
    rng = random.Random(13)
    base = simulate(5000, 0.004, 7.0, 0.99, rng)
    cases = {
        "too early (50 requests)": simulate(50, 0.004, 7.0, 0.99, rng),
        "healthy new version": simulate(500, 0.004, 7.02, 0.99, rng),
        "new version slower": simulate(500, 0.004, 7.5, 0.99, rng),
        "new prompt, worse answers": simulate(500, 0.004, 7.0, 0.90, rng),
    }
    out = {}
    for name, c in cases.items():
        out[name], why = decide(base, c)
        print(f"{name:28} -> {out[name]:8} {'; '.join(why)}")
    assert out == {"too early (50 requests)": "wait", "healthy new version": "promote",
                   "new version slower": "rollback", "new prompt, worse answers": "rollback"}
    print("ok: wait, promote, rollback, rollback")
