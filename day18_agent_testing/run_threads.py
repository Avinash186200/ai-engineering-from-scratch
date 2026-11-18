"""Run the long-thread YAML tests (tests/threads) and journeys (tests/journeys).

    python day18_agent_testing/run_threads.py                    # everything
    python day18_agent_testing/run_threads.py --thread outlook_as_of
    python day18_agent_testing/run_threads.py --thread outlook_as_of --replay   # step through by hand

Each turn prints PASS/FAIL with run_id, turn_id, tool, params and as_of.
Exit code 1 if any thread or journey fails.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from fi_agent.agent import Agent  # noqa: E402
from fi_agent.tracing import Tracer, new_run_id  # noqa: E402

THREADS_DIR = HERE / "tests" / "threads"
JOURNEYS_DIR = HERE / "tests" / "journeys"


def load_cases(threads_dir=THREADS_DIR, journeys_dir=JOURNEYS_DIR):
    cases = []
    for kind, d in (("thread", threads_dir), ("journey", journeys_dir)):
        for p in sorted(Path(d).glob("*.yaml")):
            doc = yaml.safe_load(p.read_text(encoding="utf-8"))
            doc["kind"], doc["name"], doc["path"] = kind, doc.get(kind) or p.stem, p
            cases.append(doc)
    return cases


def check_turn(spec, result):
    """Compare one turn against its YAML spec. Returns a list of failure reasons (empty = pass)."""
    reasons = []
    call = result.first_call
    actual_tool = call["name"] if call else None
    params = call["params"] if call else {}
    if actual_tool != spec.get("expect_tool"):
        reasons.append(f"tool: expected {spec.get('expect_tool')} got {actual_tool}")
    for k, v in (spec.get("expect_params") or {}).items():  # subset match
        if params.get(k) != v:
            reasons.append(f"param {k}: expected {v!r} got {params.get(k)!r}")
    if "expect_as_of" in spec and params.get("as_of") != spec["expect_as_of"]:
        reasons.append(f"as_of: expected {spec['expect_as_of']} got {params.get('as_of')}")
    out = (call or {}).get("output") or {}
    for key in spec.get("grounded_keys") or []:
        if key not in out:
            reasons.append(f"grounded: tool output has no {key}")
        elif str(out[key]) not in result.answer:
            reasons.append(f"grounded: answer missing {key}={out[key]}")
    return reasons


def run_case(case, run_id, tracer=None, replay=False, out=print):
    agent = Agent(tracer=tracer)
    rows = []
    for i, spec in enumerate(case["turns"], start=1):
        turn_id = f"{case['name']}:t{i}"
        if replay:
            cmd = input(f"\n[{turn_id}] user> {spec['user']}\n  Enter = run, e = edit text, q = quit: ").strip()
            if cmd == "q":
                break
            if cmd == "e":
                spec = {**spec, "user": input("  new text> ")}
        result = agent.turn(spec["user"], turn_id=turn_id)
        reasons = check_turn(spec, result)
        call = result.first_call or {}
        row = {"run_id": run_id, "turn_id": turn_id, "ok": not reasons, "reasons": reasons,
               "tool": call.get("name"), "params": call.get("params"), "answer": result.answer}
        rows.append(row)
        out(f"  {'PASS' if row['ok'] else 'FAIL'}  run_id={run_id} turn_id={turn_id} "
            f"tool={row['tool']} params={row['params']} as_of={(row['params'] or {}).get('as_of')}")
        for r in reasons:
            out(f"        - {r}")
        if reasons:
            want = {**(spec.get("expect_params") or {}), **({"as_of": spec["expect_as_of"]} if spec.get("expect_as_of") else {})}
            out(f"        expected call: {spec.get('expect_tool')}({want})  [params are a subset match]")
            out(f"        actual call:   {row['tool']}({row['params']})")
        if replay:
            out(f"        answer: {result.answer}")
    passed = sum(r["ok"] for r in rows)
    if case["kind"] == "journey":
        th = case.get("pass_threshold") or {"required": len(case["turns"])}
        ok = passed >= th["required"]
        out(f"  journey {case['name']}: {passed}/{len(rows)} steps passed, required {th['required']} -> "
            f"{'PASS' if ok else 'FAIL'}")
    else:
        ok = passed == len(rows) == len(case["turns"])
    return ok, rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--thread", help="run only this thread or journey name")
    ap.add_argument("--replay", action="store_true", help="interactive turn-by-turn replay")
    ap.add_argument("--trace-dir", default=str(HERE / "traces"))
    args = ap.parse_args(argv)

    cases = load_cases()
    if args.thread:
        cases = [c for c in cases if c["name"] == args.thread]
        if not cases:
            print(f"no thread or journey named {args.thread}")
            return 2
    run_id = new_run_id()
    tracer = Tracer(run_id, args.trace_dir)
    print(f"run_id={run_id}  trace={tracer.path}")
    failed = []
    for case in cases:
        print(f"\n[{case['kind']}] {case['name']}  ({case['path'].name})")
        ok, _ = run_case(case, run_id, tracer, replay=args.replay)
        if not ok:
            failed.append(case["name"])
    print(f"\n{len(cases) - len(failed)}/{len(cases)} passed" + (f"; FAILED: {', '.join(failed)}" if failed else ""))
    if failed:
        print(f"Inspect a turn: python {HERE.name}/tools/show_trace.py {run_id} --turn <turn_id>")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
