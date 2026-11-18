"""Toy fixed-income agent with multi-turn state.

Default: OFFLINE scripted rule-based "LLM" (deterministic, no API key).
Optional: LAB_LLM=anthropic uses the Anthropic SDK with tool use (see _anthropic_turn).
"""
import os
import re
from dataclasses import dataclass, field

from . import tools

# ---------------------------------------------------------------------------
# PLANTED BUG (course exercise). When True, a reference to a prior date
# ("as of that date") is resolved to the newest partial load instead of the
# carried-over conversation as_of.
DROP_CARRIED_AS_OF = True
# ---------------------------------------------------------------------------

DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
BOND_RE = re.compile(r"\b(POOL-[A-Z0-9]+)\b", re.I)
PRIOR_DATE_PHRASES = ("as of that date", "as of then", "that date", "same date")


@dataclass
class ConversationState:
    as_of: str | None = None             # carried-over as_of for the conversation
    latest_available: str | None = None  # learned from get_snapshot_date
    last_horizon: int | None = None
    last_bond: str | None = None
    history: list = field(default_factory=list)  # for the real-LLM mode


@dataclass
class TurnResult:
    answer: str
    tool_calls: list  # [{"name", "params", "output"}]

    @property
    def first_call(self):
        return self.tool_calls[0] if self.tool_calls else None


# ----------------------------- scripted LLM --------------------------------
def scripted_decide(text, state):
    """Rule-based stand-in for an LLM: returns (tool_name, params) or (None, None)."""
    t = text.lower()
    explicit = DATE_RE.search(text)
    refers_prior = any(p in t for p in PRIOR_DATE_PHRASES)

    def resolve_as_of(drop_carried=False):
        if explicit:
            return explicit.group(1)
        if refers_prior and drop_carried and state.latest_available:
            return state.latest_available  # wrong: newest partial load, not the date the user anchored to
        return state.as_of or tools.SNAPSHOT_DATE

    if ("what date" in t or "fresh" in t or "snapshot" in t) and "outlook" not in t:
        return "get_snapshot_date", {}
    if "outlook" in t or "-day" in t:
        m = re.search(r"\b(5|21)[- ]day", t)
        horizon = int(m.group(1)) if m else (state.last_horizon or 5)
        return "get_outlook", {"horizon_days": horizon, "as_of": resolve_as_of(drop_carried=DROP_CARRIED_AS_OF)}
    if any(k in t for k in ("oas", "duration", "convexity", "bond", "pool", "that one")):
        m = BOND_RE.search(text)
        bond = m.group(1).upper() if m else (state.last_bond or "POOL-A30")
        return "get_bond_metrics", {"bond_id": bond, "as_of": resolve_as_of()}
    return None, None


def scripted_answer(name, out):
    if name is None:
        return "Good morning! I can tell you the data date, the 5/21-day outlook, or bond metrics."
    if name == "get_snapshot_date":
        return (f"The latest complete snapshot is {out['snapshot_date']} ({out['age_days']} days old, "
                f"so not fresh). A partial load exists for {out['latest_available']}.")
    if name == "get_outlook":
        return (f"{out['horizon_days']}-day outlook as of {out['as_of']}: rates {out['rate_change_bp']} bp, "
                f"spreads {out['spread_change_bp']} bp (confidence {out['confidence']}).")
    return (f"{out['bond_id']} as of {out['as_of']}: OAS {out['oas_bp']} bp, effective duration "
            f"{out['eff_duration']}, convexity {out['convexity']}.")


def update_state(state, name, params, out):
    if name == "get_snapshot_date":
        state.as_of = out["snapshot_date"]
        state.latest_available = out["latest_available"]
    elif name in ("get_outlook", "get_bond_metrics"):
        if DATE_RE.fullmatch(params.get("as_of", "")) and params["as_of"] != state.latest_available:
            state.as_of = params["as_of"]
        if name == "get_outlook":
            state.last_horizon = params["horizon_days"]
        else:
            state.last_bond = params["bond_id"]


class Agent:
    def __init__(self, tracer=None, mode=None):
        self.state = ConversationState()
        self.tracer = tracer
        self.mode = mode or os.environ.get("LAB_LLM", "scripted")

    def turn(self, text, turn_id="t?"):
        tr = self.tracer
        tid = tr.trace(turn_id, "agent_turn", {"user": text, "state_in": vars_state(self.state)}) if tr else None
        if self.mode == "anthropic":
            result = _anthropic_turn(self, text, tid, turn_id)
        else:
            name, params = scripted_decide(text, self.state)
            if tr:
                tr.generation(tid, turn_id, "decide_tool", "scripted-rules",
                              {"user": text, "state": vars_state(self.state)},
                              {"tool": name, "params": params})
            calls, out = [], None
            if name:
                try:
                    out = tools.call_tool(name, params)
                    err = None
                except tools.ToolError as e:
                    out, err = {"error": str(e)}, str(e)
                if tr:
                    tr.span(tid, turn_id, f"tool:{name}", params, out, err)
                calls.append({"name": name, "params": params, "output": out})
                if err is None:
                    update_state(self.state, name, params, out)
            answer = scripted_answer(name, out) if not (out or {}).get("error") else f"Tool error: {out['error']}"
            if tr:
                tr.generation(tid, turn_id, "compose_answer", "scripted-rules", {"tool_output": out}, answer)
            result = TurnResult(answer, calls)
        if tr:
            tr.end_trace(tid, turn_id, {"answer": result.answer, "state_out": vars_state(self.state)})
        return result


def vars_state(s):
    return {"as_of": s.as_of, "latest_available": s.latest_available,
            "last_horizon": s.last_horizon, "last_bond": s.last_bond}


# ------------------------- optional real-LLM mode ---------------------------
def _anthropic_turn(agent, text, tid, turn_id):
    """Small tool-use loop with the official SDK. Needs `pip install anthropic` + ANTHROPIC_API_KEY."""
    import anthropic
    client = anthropic.Anthropic()
    model = os.environ.get("LAB_MODEL", "claude-opus-5-5")
    system = ("You answer fixed-income/MBS questions using tools only. Always pass as_of. "
              "Once the user anchors to a date, keep using it ('then', 'that date') unless told otherwise. "
              "Quote the numbers from tool output.")
    agent.state.history.append({"role": "user", "content": text})
    calls = []
    while True:
        resp = client.messages.create(model=model, max_tokens=1024, system=system,
                                      tools=tools.TOOL_SCHEMAS, messages=agent.state.history)
        if agent.tracer:
            agent.tracer.generation(tid, turn_id, "messages.create", model, {"user": text},
                                    [b.model_dump() for b in resp.content])
        agent.state.history.append({"role": "assistant", "content": resp.content})
        uses = [b for b in resp.content if b.type == "tool_use"]
        if resp.stop_reason != "tool_use" or not uses:
            answer = "".join(b.text for b in resp.content if b.type == "text")
            return TurnResult(answer, calls)
        results = []
        for u in uses:
            try:
                out, err = tools.call_tool(u.name, dict(u.input)), False
                update_state(agent.state, u.name, dict(u.input), out)
            except Exception as e:  # report tool errors back to the model
                out, err = {"error": str(e)}, True
            if agent.tracer:
                agent.tracer.span(tid, turn_id, f"tool:{u.name}", dict(u.input), out)
            calls.append({"name": u.name, "params": dict(u.input), "output": out})
            results.append({"type": "tool_result", "tool_use_id": u.id,
                            "content": str(out), "is_error": err})
        agent.state.history.append({"role": "user", "content": results})
