"""Layer 1: unit tests for the deterministic parts (the tools the LLM calls).

Most of an AI app is ordinary code: tools, parsing, validation, formatting. Test it like ordinary code:
fast, exact, many cases. A tool bug becomes a confident wrong answer, so this layer matters most.
Run:  python -m pytest day15_testing -q
"""
from __future__ import annotations

import pytest

from core.fund_model import MAX_TOP_N, rank_funds


def test_ranking_is_sorted_and_sized(a_business_day):
    out = rank_funds(a_business_day, top_n=5)
    preds = [r["predicted_return"] for r in out["top"]]
    assert len(out["top"]) == 5
    assert preds == sorted(preds, reverse=True)
    assert [r["rank"] for r in out["top"]] == [1, 2, 3, 4, 5]


def test_ranking_always_carries_the_caveat(a_business_day):
    assert "caveat" in rank_funds(a_business_day) and rank_funds(a_business_day)["caveat"]


def test_as_of_date_is_echoed(a_business_day):
    assert rank_funds(a_business_day)["as_of"] == a_business_day


@pytest.mark.parametrize("bad_date, words", [
    ("2025-06-21", "not a business day"),      # a Saturday
    ("2019-01-02", "outside the data range"),
    ("19-06-2025", "Bad date"),
    ("tomorrow", "Bad date"),
])
def test_bad_dates_are_errors_as_data_not_crashes(bad_date, words):
    out = rank_funds(bad_date)
    assert set(out) == {"error"} and words in out["error"]


@pytest.mark.parametrize("top_n", [0, -1, MAX_TOP_N + 1, True, "5", 2.5])
def test_top_n_is_validated(a_business_day, top_n):
    assert "error" in rank_funds(a_business_day, top_n=top_n)


def test_unknown_model_raises(a_business_day):
    with pytest.raises(ValueError, match="unknown model"):
        rank_funds(a_business_day, model="magic")
