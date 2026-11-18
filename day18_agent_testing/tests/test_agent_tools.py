"""Unit tests for the three tools and the conversation state."""
from __future__ import annotations

import pytest

from fi_agent import tools
from fi_agent.agent import Agent


def test_snapshot_date_is_older_than_the_partial_load():
    out = tools.get_snapshot_date()
    assert out["snapshot_date"] < out["latest_available"]
    assert out["fresh"] is False


@pytest.mark.parametrize("horizon", [5, 21])
def test_outlook_echoes_its_inputs(horizon):
    out = tools.get_outlook(horizon, "2026-11-13")
    assert out["horizon_days"] == horizon and out["as_of"] == "2026-11-13"


@pytest.mark.parametrize("args", [(10, "2026-11-13"), (5, "1999-01-01")])
def test_outlook_bad_input_is_an_error_not_a_crash(args):
    with pytest.raises(tools.ToolError):
        tools.get_outlook(*args)


def test_bond_metrics_differ_by_date():
    a = tools.get_bond_metrics("POOL-A30", "2026-11-12")
    b = tools.get_bond_metrics("POOL-A30", "2026-11-13")
    assert a["oas_bp"] != b["oas_bp"]


def test_tool_error_is_reported_in_the_answer():
    res = Agent().turn("OAS of POOL-ZZZ as of 2026-11-13?")
    assert res.answer.startswith("Tool error")


def test_explicit_date_is_carried_to_the_next_turn():
    agent = Agent()
    agent.turn("What is the OAS of POOL-A30 as of 2026-11-12?")
    res = agent.turn("and its duration?")
    assert res.first_call["params"]["as_of"] == "2026-11-12"
