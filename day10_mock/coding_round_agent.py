"""Mock coding round: a LangGraph agent that answers "What is the top fund on 2025-06-19?"

One tool (rank_funds), a fake LLM that routes by keyword (no API key), a conditional edge,
and memory with a thread id. Tool errors come back to the model as data.
Run:  python day10_mock/coding_round_agent.py
"""
import json, re
import sys
from pathlib import Path
from typing import Annotated, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.fund_model import rank_funds  # noqa: E402

def append(a: list, b: list) -> list:
    return a + b

class State(TypedDict):
    messages: Annotated[list[dict], append]
    pending: list[dict]


class FakeLLM:
    def complete(self, messages):
        last = messages[-1]
        if last["role"] == "tool":            # 2nd pass: explain
            r = json.loads(last["content"])
            if "error" in r:
                return {"text": f"I could not answer: {r['error']}", "calls": []}
            top = r["top"][0]
            return {"text": f"Top fund on {r['as_of']}: {top['fund']}, "
                            f"predicted {top['predicted_return']:+.2%}", "calls": []}
        q = last["content"].lower()           # 1st pass: decide
        if any(w in q for w in ("top", "rank", "best")):
            m = re.search(r"\d{4}-\d{2}-\d{2}", q)
            args = {"as_of": m.group() if m else None, "top_n": 3}
            return {"text": "", "calls": [{"name": "rank_funds", "args": args}]}
        return {"text": "I can only answer fund ranking questions.", "calls": []}


llm = FakeLLM()
TOOLS = {"rank_funds": rank_funds}


def llm_node(state: State) -> dict:
    out = llm.complete(state["messages"])
    return {"messages": [{"role": "assistant", "content": out["text"]}],
            "pending": out["calls"]}

def tool_node(state: State) -> dict:
    msgs = []
    for call in state["pending"]:
        try:
            result = TOOLS[call["name"]](**call["args"])
        except Exception as exc:
            result = {"error": f"{type(exc).__name__}: {exc}"}
        msgs.append({"role": "tool", "content": json.dumps(result)})
    return {"messages": msgs, "pending": []}


def route(state: State) -> str:
    return "tools" if state["pending"] else END

g = StateGraph(State)
g.add_node("llm", llm_node)
g.add_node("tools", tool_node)
g.add_edge(START, "llm")
g.add_conditional_edges("llm", route, {"tools": "tools", END: END})
g.add_edge("tools", "llm")
app = g.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    cfg = {"configurable": {"thread_id": "mock-1"}}
    for q in ["What is the top fund on 2025-06-19?", "Rank funds on 2025-06-14"]:
        out = app.invoke({"messages": [{"role": "user", "content": q}],
                          "pending": []}, config=cfg)
        print(f"Q: {q}\nA: {out['messages'][-1]['content']}\n")
    n = len(app.get_state(cfg).values["messages"])
    print(f"memory: thread mock-1 holds {n} messages")
    assert "Bharat Growth Fund" in app.get_state(cfg).values["messages"][3]["content"]
