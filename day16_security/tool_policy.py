"""A policy gate between the LLM and its tools. The model PROPOSES a tool call; this code DECIDES.

Why: an LLM can be talked into anything (prompt injection, a confused plan). So the dangerous part,
actually doing things, sits behind ordinary code that does not read prompts:
  1. Allowlist per role: which tools this USER may use (from their token, never from the prompt)
  2. Argument validation: types, ranges, allowed values; no free-form URLs or SQL
  3. Side effects need a human: anything that sends, deletes, pays or writes waits for confirmation
  4. Egress control: outbound messages only to approved destinations
  5. Rate limits per user (token bucket), so a loop or an attacker can't hammer tools
  6. Every decision logged for audit

Run:  python day16_security/tool_policy.py
"""
from __future__ import annotations

import datetime as dt
import re
import time
from dataclasses import dataclass

TOOLS = {
    "rank_funds":        {"roles": {"analyst", "admin"}, "side_effect": False},
    "lookup_definition": {"roles": {"analyst", "admin"}, "side_effect": False},
    "send_email":        {"roles": {"analyst", "admin"}, "side_effect": True},
    "delete_thread":     {"roles": {"admin"},            "side_effect": True},
}
APPROVED_EMAIL_DOMAINS = {"ourfirm.example"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_args(tool: str, args: dict) -> str | None:
    """Returns an error message, or None if the arguments are acceptable."""
    if tool == "rank_funds":
        if set(args) - {"as_of", "top_n"}:
            return f"unexpected arguments {sorted(set(args) - {'as_of', 'top_n'})}"
        if "as_of" in args and not DATE.match(str(args["as_of"])):
            return "as_of must be YYYY-MM-DD"
        top_n = args.get("top_n", 5)
        if not isinstance(top_n, int) or isinstance(top_n, bool) or not 1 <= top_n <= 20:
            return "top_n must be an integer 1..20"
    if tool == "send_email":
        to = str(args.get("to", ""))
        if to.rsplit("@", 1)[-1].lower() not in APPROVED_EMAIL_DOMAINS:
            return f"recipient domain not approved: {to}"
        if len(str(args.get("body", ""))) > 2000:
            return "body too long"
    return None


@dataclass
class Bucket:
    capacity: int = 5
    refill_per_s: float = 0.5
    tokens: float = 5
    last: float | None = None

    def take(self, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        if self.last is not None:
            self.tokens = min(self.capacity, self.tokens + max(0.0, now - self.last) * self.refill_per_s)
        self.last = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class ToolGate:
    def __init__(self):
        self.buckets: dict[str, Bucket] = {}
        self.audit: list[dict] = []

    def decide(self, user: dict, tool: str, args: dict, confirmed: bool = False, now: float | None = None) -> dict:
        def done(verdict: str, reason: str) -> dict:
            rec = {"at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "user": user["sub"],
                   "tool": tool, "verdict": verdict, "reason": reason}
            self.audit.append(rec)
            return rec

        spec = TOOLS.get(tool)
        if spec is None:
            return done("deny", "unknown tool")
        if user["role"] not in spec["roles"]:
            return done("deny", f"role {user['role']} may not use {tool}")
        if err := validate_args(tool, args):
            return done("deny", err)
        if not self.buckets.setdefault(user["sub"], Bucket()).take(now):
            return done("deny", "rate limit")
        if spec["side_effect"] and not confirmed:
            return done("needs_confirmation", f"{tool} has side effects: ask the user to confirm")
        return done("allow", "ok")


if __name__ == "__main__":
    gate = ToolGate()
    priya = {"sub": "priya", "role": "analyst"}
    cases = [
        ("rank funds, normal", priya, "rank_funds", {"as_of": "2025-06-19", "top_n": 5}, False, "allow"),
        ("SQL in the date", priya, "rank_funds", {"as_of": "2025-06-19'; DROP TABLE funds;--"}, False, "deny"),
        ("analyst deletes a thread", priya, "delete_thread", {"id": "c-202"}, False, "deny"),
        ("email to an outside domain", priya, "send_email", {"to": "x@attacker.example", "body": "data"}, False, "deny"),
        ("email inside, not confirmed", priya, "send_email", {"to": "boss@ourfirm.example", "body": "hi"}, False, "needs_confirmation"),
        ("email inside, user confirmed", priya, "send_email", {"to": "boss@ourfirm.example", "body": "hi"}, True, "allow"),
        ("a tool that doesn't exist", priya, "run_shell", {"cmd": "ls"}, False, "deny"),
    ]
    for name, user, tool, args, conf, want in cases:
        got = gate.decide(user, tool, args, conf, now=0.0)
        print(f"  {name:30} -> {got['verdict']:18} {got['reason']}")
        assert got["verdict"] == want, name
    rahul = {"sub": "rahul", "role": "analyst"}
    burst = [gate.decide(rahul, "lookup_definition", {}, now=100.0)["verdict"] for _ in range(8)]
    print("  8 calls in the same second    ->", burst)
    assert burst.count("allow") == 5 and burst[-1] == "deny"
    print(f"ok: {len(gate.audit)} decisions logged for audit")
