"""A LangGraph agent: tools, a conditional edge, reducers, memory, a round limit and a give-up node.

Run:  python day03_agents/agent.py                       (FakeLLM, no key)
      python day03_agents/agent.py --real                (Claude via the adapter)
      python day03_agents/agent.py --ask "Which funds look best on 2025-06-20?"
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.fund_model import fund_info, lookup_definition, model_info, rank_funds  # noqa: E402
from core.llm import ClaudeLLM, FakeLLM, final_text  # noqa: E402

SYSTEM = (ROOT / "day02_prompting" / "system_prompt.md").read_text(encoding="utf-8")
MAX_ROUNDS = 5

TOOLS = [
    {
      "name": "rank_funds",
      "description": (
        "Rank mutual funds by predicted return for one as-of date. "
        "Use for questions about which funds look attractive, "
        "rankings, scores or predicted returns. "
        "Dates must be YYYY-MM-DD business days."),
      "input_schema": {
        "type": "object",
        "properties": {
          "as_of": {"type": "string", "description": "YYYY-MM-DD"},
          "top_n": {"type": "integer", "description": "How many funds"},
          "model": {"type": "string", "enum": ["quantile", "ridge"],
                    "description": "Which ranking model; default quantile"}
        },
        "required": []
      }
    },
    {"name": "lookup_definition",
     "description": "Define a mutual fund term such as NAV, SIP, expense ratio or exit load.",
     "input_schema": {"type": "object", "properties": {"term": {"type": "string"}},
                      "required": ["term"]}},
    {"name": "model_info",
     "description": "Facts about the ranking models: features, target, training window.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "fund_info",
     "description": "Latest facts (category, NAV, expense ratio, AUM) for one fund by exact name.",
     "input_schema": {"type": "object", "properties": {"name": {"type": "string"}},
                      "required": ["name"]}},
]
TOOL_FUNCS = {"rank_funds": rank_funds, "lookup_definition": lookup_definition,
              "model_info": model_info, "fund_info": fund_info}


def append(a: list, b: list) -> list:      # reducer: new items are added, never replace
    return a + b


class State(TypedDict):
    messages: Annotated[list[dict], append]   # history: added to
    pending_calls: list[dict]                 # tool calls just requested
    tools_called: Annotated[list[str], append]
    tool_rounds: int                          # counter for the limit


llm = FakeLLM()                               # replaced by build_app(llm)


def trim_for_model(messages, keep_turns=2):
    starts = [i for i, m in enumerate(messages)
              if m["role"] == "user" and isinstance(m["content"], str)]
    if len(starts) <= keep_turns:
        return messages
    return messages[starts[-keep_turns]:]


def llm_node(state: State) -> dict:        # reads the whole state
    out = llm.complete(SYSTEM, trim_for_model(state["messages"]), TOOLS)
    blocks = [{"type": "text", "text": out["text"]}] if out["text"] else []
    blocks += [{"type": "tool_use", **c} for c in out["tool_calls"]]
    reply = {"role": "assistant", "content": blocks}
    return {"messages": [reply],                # returns only
            "pending_calls": out["tool_calls"]} # what changed


def tool_node(state: State) -> dict:
    results = []
    for call in state["pending_calls"]:
        fn = TOOL_FUNCS.get(call["name"])
        try:
            if fn is None:
                result = {"error": f"unknown tool {call['name']}"}
            else:
                result = fn(**call["input"])
        except Exception as exc:
            result = {"error": f"{type(exc).__name__}: {exc}"}
        results.append({"type": "tool_result", "tool_use_id": call["id"],
                        "content": json.dumps(result)})
    return {"messages": [{"role": "user", "content": results}],
            "pending_calls": [], "tool_rounds": state["tool_rounds"] + 1,
            "tools_called": [c["name"] for c in state["pending_calls"]]}


def run_one(call):
    fn = TOOL_FUNCS.get(call["name"])
    try:
        result = fn(**call["input"]) if fn else {"error": "unknown tool"}
    except Exception as exc:
        result = {"error": f"{type(exc).__name__}: {exc}"}
    return {"type": "tool_result", "tool_use_id": call["id"],
            "content": json.dumps(result)}


def parallel_tool_node(state: State) -> dict:
    """Same job as tool_node, but independent calls run at the same time."""
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run_one, state["pending_calls"]))
    return {"messages": [{"role": "user", "content": results}],
            "pending_calls": [], "tool_rounds": state["tool_rounds"] + 1,
            "tools_called": [c["name"] for c in state["pending_calls"]]}


def give_up_node(state: State) -> dict:
    skipped = [{"type": "tool_result", "tool_use_id": c["id"],
                "content": json.dumps({"error": "not run: round limit reached"})}
               for c in state["pending_calls"]]
    note = ("I stopped after the maximum number of tool rounds. "
            "Please narrow the question.")
    return {"messages": [{"role": "user", "content": skipped},
                         {"role": "assistant", "content": note}],
            "pending_calls": []}


def route(state: State) -> str:
    if state["pending_calls"] and state.get("tool_rounds", 0) < MAX_ROUNDS:
        return "tools"
    if state["pending_calls"]:                 # limit hit and calls pending
        return "give_up"
    return END


def build_app(model, checkpointer=None, interrupt_before=None, parallel=False):
    global llm
    llm = model
    g = StateGraph(State)
    g.add_node("llm", llm_node)
    g.add_node("tools", parallel_tool_node if parallel else tool_node)
    g.add_node("give_up", give_up_node)
    g.add_edge(START, "llm")                                  # entry
    g.add_conditional_edges("llm", route, {"tools": "tools", "give_up": "give_up", END: END})
    g.add_edge("tools", "llm")                                # always back
    g.add_edge("give_up", END)
    return g.compile(checkpointer=checkpointer or MemorySaver(),
                     interrupt_before=interrupt_before)


def ask(app, question: str, thread_id: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    before = len(app.get_state(config).values.get("tools_called", []))
    result = app.invoke(
        {"messages": [{"role": "user", "content": question}],
         "pending_calls": [], "tool_rounds": 0},
        config=config,
    )
    return {"answer": final_text(result["messages"]),
            "tools_called": result.get("tools_called", [])[before:]}


def demo(app):
    for q in ["Which funds look best on 2025-06-20?",
              "What is an expense ratio?",
              "Which funds look best on 2025-06-21?"]:          # a Saturday: error as data
        out = ask(app, q, thread_id="priya-1")
        print(f"Q: {q}\n   tools: {out['tools_called']}\nA: {out['answer']}\n")

    q = "Rank funds on 2025-06-20, and what is an expense ratio?"   # two halves, two tools
    out = ask(app, q, thread_id="rahul-2")
    print(f"Q: {q}\n   tools: {out['tools_called']}\nA: {out['answer']}\n")

    cfg = {"configurable": {"thread_id": "priya-1"}}
    snap = app.get_state(cfg)                 # latest snapshot for this thread
    msgs = snap.values["messages"]
    print(f"memory: priya-1 holds {len(msgs)} messages; next={snap.next} (() means finished)")
    rahul = app.get_state({"configurable": {"thread_id": "rahul-1"}}).values.get("messages", [])
    print(f"memory: rahul-1 holds {len(rahul)} messages (a new thread starts fresh)")
    print(f"trim_for_model keeps the last {len(trim_for_model(msgs))} messages of {len(msgs)}")
    print(f"snapshots saved for priya-1: {len(list(app.get_state_history(cfg)))}")

    print("\nFailures come back as data:")
    calls = [{"id": "call_1", "name": "rank_funds", "input": {"as_of": "2025-06-21"}},
             {"id": "call_2", "name": "rank_funds", "input": {"as_of": "2025-06-20", "model": "xgboost"}},
             {"id": "call_3", "name": "get_prices", "input": {}}]
    for r in tool_node({"pending_calls": calls, "tool_rounds": 0})["messages"][0]["content"]:
        print(f"  {r['tool_use_id']}: {r['content']}")

    print("\nStreaming updates for one question:")
    inp = {"messages": [{"role": "user", "content": "What is an expense ratio?"}],
           "pending_calls": [], "tool_rounds": 0}
    for event in app.stream(inp, {"configurable": {"thread_id": "stream-1"}}, stream_mode="updates"):
        for node, update in event.items():
            print(f"  UPDATE from {node:<5} -> {sorted(update)}")


def breakpoint_demo(model):
    app = build_app(model, interrupt_before=["tools"])
    cfg = {"configurable": {"thread_id": "review-1"}}
    first_input = {"messages": [{"role": "user", "content": "Which funds look best on 2025-06-20?"}],
                   "pending_calls": [], "tool_rounds": 0}
    app.invoke(first_input, cfg)
    print("\nBreakpoint before tools:")
    print("  next:", app.get_state(cfg).next)                       # ('tools',)  paused
    print("  pending_calls:", app.get_state(cfg).values["pending_calls"])
    out = app.invoke(None, cfg)                                       # None = carry on
    print("  after resume:", final_text(out["messages"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--ask")
    args = ap.parse_args()
    model = ClaudeLLM() if args.real else FakeLLM()
    app = build_app(model)
    if args.ask:
        print(ask(app, args.ask, thread_id="cli-1"))
    else:
        demo(app)
        breakpoint_demo(model)
