"""Mock coding round: build a tool-calling agent loop from scratch in ~60 lines (no framework).

Task: given a question, let the "LLM" request tools, run them, feed results back, stop
when it answers or after MAX_STEPS. Tool errors must come back as data.
Run:  python day10_mock/coding_round_agent.py
"""
import json

MAX_STEPS = 5

NAV = {"Bharat Growth Fund": 41.2, "Deccan Bond Fund": 18.7, "Nifty Value Fund": 33.9}


def get_nav(fund: str) -> dict:
    if fund not in NAV:
        return {"error": f"unknown fund {fund}"}
    return {"fund": fund, "nav": NAV[fund]}


def units_for(amount: float, nav: float) -> dict:
    if nav <= 0:
        return {"error": "nav must be positive"}
    return {"units": round(amount / nav, 3)}


TOOLS = {"get_nav": get_nav, "units_for": units_for}


def fake_llm(history):
    """Scripted policy: look up NAV, then compute units, then answer."""
    tool_msgs = [m for m in history if m["role"] == "tool"]
    if not tool_msgs:
        return {"tool": "get_nav", "args": {"fund": "Deccan Bond Fund"}}
    last = json.loads(tool_msgs[-1]["content"])
    if "error" in last:
        return {"answer": f"Sorry: {last['error']}"}
    if "nav" in last:
        return {"tool": "units_for", "args": {"amount": 10000, "nav": last["nav"]}}
    return {"answer": f"10,000 rupees buys {last['units']} units of Deccan Bond Fund."}


def run_agent(question, llm=fake_llm):
    history = [{"role": "user", "content": question}]
    for step in range(1, MAX_STEPS + 1):
        action = llm(history)
        if "answer" in action:
            return action["answer"], step
        fn = TOOLS.get(action["tool"])
        try:
            result = fn(**action["args"]) if fn else {"error": f"no tool {action['tool']}"}
        except Exception as e:
            result = {"error": str(e)}
        print(f"  step {step}: {action['tool']}({action['args']}) -> {result}")
        history.append({"role": "tool", "content": json.dumps(result)})
    return "Stopped: step limit reached", MAX_STEPS


if __name__ == "__main__":
    answer, steps = run_agent("How many units of Deccan Bond Fund do I get for 10,000 rupees?")
    print(f"answer after {steps} steps: {answer}")
    assert "units" in answer
    looping = lambda h: {"tool": "get_nav", "args": {"fund": "Deccan Bond Fund"}}  # noqa: E731
    print("looping model ->", run_agent("loop forever", looping))
