"""Run the golden set through the real Day 3 agent and gate on the pass rate.

Exit code 0 if the pass rate >= THRESHOLD (90%), else 1, so CI can block a bad change.
Run:  python day06_evals/eval_harness.py            (FakeLLM, no key)
      python day06_evals/eval_harness.py --real     (Claude)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "day03_agents"))
from agent import ask, build_app  # noqa: E402
from core.llm import ClaudeLLM, FakeLLM  # noqa: E402

THRESHOLD = 0.9


def run(real: bool) -> float:
    golden = json.loads((HERE / "golden_set.json").read_text(encoding="utf-8"))
    app = build_app(ClaudeLLM() if real else FakeLLM())
    passed = 0
    failures = []
    print(f"{'case':<15} {'tool':<6} {'grounded':<9} {'clean':<6} result")
    print("-" * 51)
    for case in golden:
        out = ask(app, case["question"], thread_id=f"eval-{case['id']}")
        ans = out["answer"].lower()
        tool_ok  = case["expected_tool"] in out["tools_called"]
        grounded = all(s.lower() in ans for s in case["must_contain"])
        clean    = not any(s.lower() in ans for s in case["must_not_contain"])
        passed  += tool_ok and grounded and clean
        ok = tool_ok and grounded and clean
        print(f"{case['id']:<15} {tool_ok!s:<6} {grounded!s:<9} {clean!s:<6} {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append((case, out))
    rate = passed / len(golden)
    print(f"\npass rate {passed}/{len(golden)} = {rate:.0%}  (threshold {THRESHOLD:.0%})")
    for case, out in failures:                     # why it failed, readable in the CI log
        print(f"\nFAIL {case['id']}: tools={out['tools_called']}\n  answer: {out['answer']}")
    return rate


if __name__ == "__main__":
    rate = run(real="--real" in sys.argv)
    sys.exit(0 if rate >= THRESHOLD else 1)
