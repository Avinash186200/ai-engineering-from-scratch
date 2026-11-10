"""Layer 4: testing the LLM-driven behaviour without flaky exact-text assertions.

Rules for testing non-deterministic output:
  - Assert on STRUCTURE and FACTS, not wording: which tool was called, with what arguments,
    that numbers in the answer are grounded, that the caveat is present, that JSON parses.
  - Use a fake/stub model in unit tests (fast, free, deterministic). Real-model quality is measured
    by the eval suite (Day 6) on a golden set, with a pass-rate threshold, not by unit tests.
"""
from __future__ import annotations

import json
import re

from core.fund_model import rank_funds
from core.llm import FakeLLM
from day12_llmops.guards import run_all

TOOLS = [{"name": "rank_funds", "description": "rank funds", "input_schema": {"type": "object"}},
         {"name": "lookup_definition", "description": "define a term", "input_schema": {"type": "object"}}]


def test_ranking_question_calls_rank_funds_with_the_date():
    out = FakeLLM().complete("system", [{"role": "user", "content": "Which funds look best on 2025-06-19?"}], TOOLS)
    calls = out["tool_calls"]
    assert [c["name"] for c in calls] == ["rank_funds"]
    assert calls[0]["input"].get("as_of") == "2025-06-19"


def test_definition_question_does_not_call_the_ranking_tool():
    out = FakeLLM().complete("system", [{"role": "user", "content": "What is an exit load?"}], TOOLS)
    assert "rank_funds" not in [c["name"] for c in out["tool_calls"]]


def test_final_answer_is_grounded_in_the_tool_result():
    result = rank_funds("2025-06-19", top_n=3)
    msgs = [{"role": "user", "content": "Which funds look best on 2025-06-19?"},
            {"role": "assistant", "content": [{"type": "tool_use", "id": "call_1", "name": "rank_funds", "input": {}}]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_1", "content": json.dumps(result)}]}]
    answer = FakeLLM().complete("system", msgs, TOOLS)["text"]
    assert answer.strip()
    checks = run_all(answer, result["top"])
    assert next(c for c in checks["checks"] if c["check"] == "grounded_numbers")["pass"], checks
    named = re.findall(r"\d\. ([A-Z][\w ]*? Fund)", answer)
    assert named, "the answer should name the funds it ranks"
    assert set(named) <= {r["fund"] for r in result["top"]}     # no invented funds
    assert result["caveat"] in answer                            # the caveat survives into the answer
