"""Run the golden set through the day03 agent and gate on the pass rate.

Exit code 0 if pass rate >= --min-pass (default 0.9), else 1 - so CI can block a bad change.
Run:  python day06_evals/eval_harness.py            (FakeLLM)
      python day06_evals/eval_harness.py --real     (Claude)
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "day03_agents"))
from agent import build_graph  # noqa: E402
from core.llm import get_llm  # noqa: E402

GOLDEN = Path(__file__).with_name("golden_set.json")


def run_case(app, case):
    cfg = {"configurable": {"thread_id": case["id"]}}
    state = app.invoke({"messages": [{"role": "user", "content": case["question"]}], "steps": 0}, cfg)
    used = [c["name"] for m in state["messages"] if m["role"] == "assistant" for c in m.get("tool_calls", [])]
    answer = state["messages"][-1]["content"]
    problems = []
    if sorted(set(used)) != sorted(case["expect_tools"]):
        problems.append(f"tools {used} != {case['expect_tools']}")
    problems += [f"missing '{s}'" for s in case.get("must_contain", []) if s.lower() not in answer.lower()]
    problems += [f"leaked '{s}'" for s in case.get("must_not_contain", []) if s.lower() in answer.lower()]
    return problems, answer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--min-pass", type=float, default=0.9)
    args = ap.parse_args()
    app = build_graph(get_llm(args.real))
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))
    passed = 0
    for case in cases:
        problems, answer = run_case(app, case)
        passed += not problems
        print(f"{'PASS' if not problems else 'FAIL'}  {case['id']:<18} {'; '.join(problems) or answer[:60]}")
    rate = passed / len(cases)
    print(f"\npass rate {passed}/{len(cases)} = {rate:.0%} (gate {args.min_pass:.0%})")
    sys.exit(0 if rate >= args.min_pass else 1)


if __name__ == "__main__":
    main()
