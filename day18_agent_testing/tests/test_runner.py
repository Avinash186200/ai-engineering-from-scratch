"""The runner must catch the planted bug, and only it.

The planted failure in outlook_as_of turn 3 is EXPECTED. These tests assert the runner
detects it, so pytest stays green while `run_threads.py` exits 1.
"""
from __future__ import annotations

import run_threads
from fi_agent.agent import TurnResult


def _cases():
    return {c["name"]: c for c in run_threads.load_cases()}


def _run(name, tmp_path):
    from fi_agent.tracing import Tracer
    tracer = Tracer("pytest-run", tmp_path)
    return run_threads.run_case(_cases()[name], "pytest-run", tracer, out=lambda *_: None)


def test_there_are_at_least_three_threads_and_one_journey():
    kinds = [c["kind"] for c in run_threads.load_cases()]
    assert kinds.count("thread") >= 3 and kinds.count("journey") >= 1


def test_planted_bug_is_detected_at_turn_3_only(tmp_path):
    ok, rows = _run("outlook_as_of", tmp_path)
    assert not ok
    failing = [r for r in rows if not r["ok"]]
    assert [r["turn_id"] for r in failing] == ["outlook_as_of:t3"]
    assert failing[0]["tool"] == "get_outlook"
    assert failing[0]["params"]["as_of"] == "2026-11-14"          # actual: newest partial load
    assert "as_of: expected 2026-11-13 got 2026-11-14" in failing[0]["reasons"]


def test_other_threads_pass(tmp_path):
    for name in ("bond_followup", "explicit_dates"):
        ok, _ = _run(name, tmp_path)
        assert ok, name


def test_almost_passing_journey_is_a_fail(tmp_path):
    ok, rows = _run("morning_check", tmp_path)
    assert sum(r["ok"] for r in rows) == 4 and not ok


def test_after_the_fix_everything_passes(fixed_agent, tmp_path):
    for name in _cases():
        ok, rows = _run(name, tmp_path)
        assert ok, (name, [r["reasons"] for r in rows if not r["ok"]])


def test_main_exit_code_is_nonzero_on_failure(tmp_path, capsys):
    assert run_threads.main(["--trace-dir", str(tmp_path)]) == 1
    assert run_threads.main(["--thread", "bond_followup", "--trace-dir", str(tmp_path)]) == 0
    assert "turn_id=bond_followup:t1" in capsys.readouterr().out


def test_grounding_check_catches_an_invented_number():
    spec = {"expect_tool": "get_outlook", "grounded_keys": ["rate_change_bp"]}
    call = {"name": "get_outlook", "params": {}, "output": {"rate_change_bp": -2.4}}
    assert check_ok(spec, TurnResult("rates -2.4 bp", [call]))
    assert not check_ok(spec, TurnResult("rates -9.9 bp", [call]))


def check_ok(spec, result):
    return not run_threads.check_turn(spec, result)


def test_trace_tree_shows_the_divergent_call(tmp_path):
    from tools.show_trace import load, render
    _run("outlook_as_of", tmp_path)
    tree = render(load("pytest-run", tmp_path), "outlook_as_of:t3")
    assert "SPAN tool:get_outlook" in tree and '"as_of": "2026-11-14"' in tree
    assert '"as_of": "2026-11-13"' in tree  # state_in still held the right date
