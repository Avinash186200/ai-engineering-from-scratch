"""Online checks that run on every answer, before the user sees it.

You cannot label every production answer by hand, so you use cheap automatic signals:
  1. grounded_numbers - every number in the answer must appear in the tool results it was built from
  2. cites_known_funds - every fund the answer names must exist in the tool results
  3. is_refusal       - the model said "I can't help" (track the rate: a jump means a broken prompt or tool)
  4. leaks_pii        - the answer contains an email, phone number, tax ID or key

Each check is a signal, not proof. Flagged answers go to a review queue; the RATE goes to a dashboard.
An LLM-as-judge check (see judge_prompt) is slower and costs money, so run it on a sample.

Run:  python day12_llmops/guards.py
"""
from __future__ import annotations

import json
import re

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from day12_llmops.tracing import EMAIL, KEY, PAN, PHONE

NUM = re.compile(r"[-+]?\d+(?:\.\d+)?")
REFUSAL = re.compile(r"\b(i can(?:'|no)t|i am unable|i'm unable|i don't have (?:access|information))\b", re.I)


def _numbers(text: str) -> set[float]:
    return {round(abs(float(n)), 4) for n in NUM.findall(text)}


def grounded_numbers(answer: str, tool_results: list[dict], pct_ok: bool = True) -> dict:
    """Numbers in the answer that are NOT in the evidence are possible hallucinations.
    pct_ok: 0.0099 in the data may be written as 0.99% in the answer."""
    evidence = _numbers(json.dumps(tool_results))
    if pct_ok:
        evidence |= {round(x * 100, 2) for x in evidence} | {round(x * 100, 4) for x in evidence}
    claimed = _numbers(answer)
    ignore = {float(i) for i in range(0, 32)} | {2020.0, 2021.0, 2022.0, 2023.0, 2024.0, 2025.0}  # counts, days, years
    missing = sorted(n for n in claimed - ignore if n not in evidence)
    return {"check": "grounded_numbers", "pass": not missing, "unsupported": missing}


def cites_known_funds(answer: str, tool_results: list[dict], pattern: str = r"\bFund [A-Z][A-Za-z]*\b") -> dict:
    known = set(re.findall(pattern, json.dumps(tool_results)))
    named = set(re.findall(pattern, answer))
    unknown = sorted(named - known)
    return {"check": "cites_known_funds", "pass": not unknown, "unknown": unknown}


def is_refusal(answer: str) -> dict:
    return {"check": "is_refusal", "pass": not REFUSAL.search(answer)}


def leaks_pii(answer: str) -> dict:
    hits = [n for n, rx in (("email", EMAIL), ("phone", PHONE), ("pan", PAN), ("secret", KEY)) if rx.search(answer)]
    return {"check": "leaks_pii", "pass": not hits, "found": hits}


def run_all(answer: str, tool_results: list[dict]) -> dict:
    checks = [grounded_numbers(answer, tool_results), cites_known_funds(answer, tool_results),
              is_refusal(answer), leaks_pii(answer)]
    return {"pass": all(c["pass"] for c in checks), "checks": checks}


def judge_prompt(question: str, answer: str, evidence: list[dict]) -> str:
    """Prompt for an LLM-as-judge groundedness score. Run it on a SAMPLE (say 5%) of traffic,
    and calibrate it against human labels before trusting it."""
    return ("You are checking an answer for faithfulness.\n"
            f"Question: {question}\nEvidence (the only facts allowed): {json.dumps(evidence)}\n"
            f"Answer: {answer}\n"
            'Reply with JSON only: {"grounded": true|false, "unsupported_claims": ["..."]}')


if __name__ == "__main__":
    evidence = [{"rank": 1, "fund": "Fund Alpha", "predicted_return": 0.0099},
                {"rank": 2, "fund": "Fund Beta", "predicted_return": 0.0081}]
    cases = {
        "good": "Fund Alpha ranks first with a predicted return of 0.99% over 20 days, then Fund Beta at 0.81%.",
        "made-up number": "Fund Alpha ranks first with a predicted return of 2.4%.",
        "made-up fund": "Fund Alpha and Fund Zeta look best.",
        "refusal": "I can't help with that request.",
        "pii leak": "Sent the list to priya@example.com.",
    }
    for name, ans in cases.items():
        r = run_all(ans, evidence)
        failed = [c for c in r["checks"] if not c["pass"]]
        print(f"{name:15} pass={r['pass']!s:5} {failed if failed else ''}")
    assert run_all(cases["good"], evidence)["pass"]
    assert not any(run_all(cases[k], evidence)["pass"] for k in cases if k != "good")
    print("ok: the good answer passes, all four bad answers are caught")
