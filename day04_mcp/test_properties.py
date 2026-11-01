"""Property-based tests for the ranking tool (pip install hypothesis pytest).

Run:  python -m pytest day04_mcp/test_properties.py -q
"""
import sys
from pathlib import Path

from hypothesis import given, settings, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.fund_model import rank_funds  # noqa: E402


@settings(max_examples=200, deadline=None)
@given(day=st.dates(), top_n=st.integers(1, 20))
def test_ranking_rules(day, top_n):
    out = rank_funds(day.isoformat(), top_n)   # must never raise
    if "error" in out:
        return                                  # errors are data
    ranks = [r["rank"] for r in out["top"]]
    assert ranks == list(range(1, len(ranks) + 1))
    rets = [r["predicted_return"] for r in out["top"]]
    assert rets == sorted(rets, reverse=True)


@settings(max_examples=100, deadline=None)
@given(day=st.dates(min_value=__import__("datetime").date(2020, 1, 1),
                    max_value=__import__("datetime").date(2025, 6, 30)))
def test_in_range_weekdays_always_rank(day):
    out = rank_funds(day.isoformat(), 5)
    assert ("error" in out) == (day.weekday() >= 5)
    if "error" not in out:
        assert out["caveat"] and out["n_scored"] >= len(out["top"])
