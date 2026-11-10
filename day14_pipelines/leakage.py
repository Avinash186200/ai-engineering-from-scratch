"""Look-ahead leakage: the same model looks much better when it is (accidentally) fed the future.

Task: at the end of each month, predict next month's value of a target that depends on the indicator.
Two ways to build the training table:
  NAIVE         - join on value_date and use today's database (final, revised numbers, including the
                  current month, which was not even published yet). This is what a quick SQL join does.
  POINT-IN-TIME - use only what was public at the end of that month (as_of / latest_known).

Same data, same model (a straight line). Only the join differs.

Run:  python day14_pipelines/leakage.py
"""
from __future__ import annotations

import random
import statistics
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from day14_pipelines.pipeline import connect, ingest, latest_known, source_feed


def corr(a: list[float], b: list[float]) -> float:
    return statistics.correlation(a, b)


def build(months: int = 120, seed: int = 7):
    con = connect()
    feed = source_feed("2015-01", months, seed=seed)
    ingest(con, feed, "load")
    final = {r["value_date"]: r["value"] for r in feed if r["vintage"] == "revised"}
    rng = random.Random(seed + 1)
    # the thing we predict: next month's target is driven by THIS month's true indicator
    target = {ym: 0.8 * final[ym] + rng.gauss(0, 0.6) for ym in final}
    return con, final, target


def evaluate(con, final, target):
    naive_x, pit_x, y = [], [], []
    yms = sorted(final)
    for ym in yms[2:-1]:
        month_end = f"{ym}-28"
        naive_x.append(final[ym])                                   # the future leaks in
        pit_x.append(latest_known(con, "indicator", month_end)[1])  # what we really knew
        y.append(target[ym])
    return corr(naive_x, y), corr(pit_x, y), len(y)


if __name__ == "__main__":
    con, final, target = build()
    naive, pit, n = evaluate(con, final, target)
    print(f"{n} monthly predictions")
    print(f"  naive join (today's revised data):  correlation {naive:.2f},  R^2 {naive**2:.2f}")
    print(f"  point-in-time (what was known):     correlation {pit:.2f},  R^2 {pit**2:.2f}")
    print(f"\nThe naive version looks {naive**2 / max(pit**2, 1e-9):.1f}x better. None of that edge exists in real life.")
    assert naive > 0.7 and pit < naive - 0.3
    print("ok: look-ahead inflates the result; the point-in-time number is the honest one")
