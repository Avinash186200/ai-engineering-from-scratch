# Day 3, Part 4: When AI Agents Fail: Tool Errors, Loop Limits, Retries

**Watch:** [youtu.be/1_qBo7pXOcg](https://youtu.be/1_qBo7pXOcg) · **Code:** [`day03_agents/`](../day03_agents/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Real agents fail: bad arguments, missing data, tools that don't exist, models that loop forever. In this episode we make our research assistant's agent fail safely, every time.

## What you will learn

- Why tool errors must be returned as results, not raised
- How to write error messages the model can act on
- Bounded loops: why every agent needs a hard round limit, and what it saves in cost
- Retries with exponential backoff, and when NOT to retry
- Parallel tool calls: running several tools at once

## Chapters

- [0:00](https://youtu.be/1_qBo7pXOcg?t=0) Intro
- [0:48](https://youtu.be/1_qBo7pXOcg?t=48) Tool errors are results, not exceptions
- [1:54](https://youtu.be/1_qBo7pXOcg?t=114) Three failures, handled
- [3:19](https://youtu.be/1_qBo7pXOcg?t=199) Bounded loops
- [3:49](https://youtu.be/1_qBo7pXOcg?t=229) What a loop costs
- [5:30](https://youtu.be/1_qBo7pXOcg?t=330) Retries with backoff
- [6:59](https://youtu.be/1_qBo7pXOcg?t=419) Parallel tool calls

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In part three, we saw how our agent remembers conversations with thread ids and checkpoints. Now the part that separates a demo from a real product: what happens when things go wrong.

As always, watch at one point two five times speed if this feels slow.

There are four big ways an agent fails. A tool fails, because of a bad argument or missing data. The model gets stuck in a loop. The network blips. Or it is simply slow, because tools run one after another. We will fix each one in turn.

**Four ways an agent fails**

- A tool fails: bad argument, missing data, unknown tool
- The model loops: calls tools forever, never answers
- The network blips: rate limits, timeouts, overloaded servers
- Calls are slow: several tools, run one after another

## Tool errors are results, not exceptions

First, tool errors. When a tool fails, you have two choices, and only one is right.

Option one: let the exception escape. The whole request crashes, and the user sees an error page. Option two: catch it, and return the error as the tool's result. The model reads it, just like any other result, and responds: it explains the problem, asks the user, or tries something else. Agents should always do the second.

**Raise it, or return it?**

- **Raise the exception**
  - The whole request crashes
  - The user sees an error page
  - The model never learns what happened
- **Return it as a result**
  - The model reads the error
  - It explains, asks, or tries again
  - The user gets a clear sentence

*Agents should always return the error.*

Here is the tools node in agent dot py. For each pending call, it looks up the function by name. If the name does not exist, that becomes an error result. If the function raises an exception, we catch it and turn it into an error result too. Either way, the model gets an answer for every request, with the matching id.

**Catching failures as data**

`day03_agents/agent.py`
```python
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
            "pending_calls": [], "tool_rounds": state["tool_rounds"] + 1}
```

Let's look at three failures. First, Priya asks for rankings on twenty first June, twenty twenty five. That was a Saturday, so there is no data. The ranking tool returns an error saying, not a business day, try a nearby weekday. The model sees it and tells her plainly. No crash, and no invented ranking.

Second, a bad argument: the model asks for a ranking model called xgboost, which does not exist. Third, the model asks for a tool called get prices, which we never defined. Notice the second message names the valid choices. A real model reading it will very likely retry with a correct one. Good error messages are instructions for the model.

**What the model sees**

| Situation | Tool result returned |
|---|---|
| Weekend date | {"error": "No data for 2025-06-21 (not a business day?). Try a nearby weekday."} |
| Bad argument | {"error": "ValueError: unknown model 'xgboost'; choose one of ['ridge', 'quantile']"} |
| Tool doesn't exist | {"error": "unknown tool get_prices"} |

*Good error messages are instructions for the model.*

Watch out for two opposite mistakes. One, letting exceptions escape. Two, swallowing the error and returning an empty result, so the model thinks there is simply no data, and may invent an answer to fill the gap. And never leak secrets: a database address in an error message would be shown to the model, and maybe to the user.

**Two opposite mistakes, and one leak**

- Letting exceptions escape: one bad argument kills the request
- Swallowing the error: an empty result, so the model may invent an answer
- Leaking secrets: a database address with a password in the error text

*Return the error, clearly labelled. Tell the model to report it.*

## Bounded loops

Second failure: the model gets stuck in a loop.

A model can get stuck, calling the same tool again and again, or bouncing between two tools without ever answering. Each round is another model call, and the whole growing history is sent again every time. So cost climbs fast. A hard limit caps the damage, and lets you say what the worst case is.

**Every agent needs a hard round limit**

- A model can call the same tool again and again, never answering
- Every round resends the whole growing history: cost climbs fast
- A stuck request ties up a server
- With a limit, you can state the worst case

Some illustrative numbers. Say the prompt, tools and question are about two thousand tokens, and each round adds fifteen hundred more. Two rounds means three model calls and about ten thousand input tokens. Five rounds means six calls and about thirty five thousand. Two and a half times the rounds, but more than three times the cost.

**Why rounds get expensive**

| Rounds | Model calls | Input tokens | Cost at $3 per million |
|---|---|---|---|
| 2 | 3 | 10,650 | about 3 cents |
| 5 | 6 | 34,800 | about 10 cents |

*History is resent every call: cost grows faster than the number of rounds.*

If you have done some machine learning, the round limit is like max iter when fitting a model: a guard against never converging. The difference is that there is no loss going down here. The loop stops only when the model chooses to answer, so the hard limit matters even more.

**Like max_iter**

> **The round limit is max_iter for agents.**
> A guard against never converging. But there is no loss going down: the model stops only when it chooses to answer.

Now, a gap worth noticing in our simple agent. When the limit stops the loop, the last saved message is a tool request with no matching result. The user gets an empty reply. And with a real provider, the next question on that thread gets rejected, because every tool request must be answered.

**What happens when the limit hits?**

- The last saved message is a tool request with no answer
- The user gets an empty reply
- A real provider rejects the next question on that thread

The fix is a small give up node. It answers every open request with an error saying, not run, round limit reached, so the history stays well formed. Then it adds a clear note for the user: I stopped after the maximum rounds, please narrow the question. The route function sends us here instead of straight to end.

**A give_up node**

`day03_agents/agent.py`
```python
def give_up_node(state: State) -> dict:
    skipped = [{"type": "tool_result", "tool_use_id": c["id"],
                "content": json.dumps({"error": "not run: round limit reached"})}
               for c in state["pending_calls"]]
    note = ("I stopped after the maximum number of tool rounds. "
            "Please narrow the question.")
    return {"messages": [{"role": "user", "content": skipped},
                         {"role": "assistant", "content": note}],
            "pending_calls": []}

# in route(): if the limit is hit and calls are pending -> "give_up"
g.add_node("give_up", give_up_node)
g.add_edge("give_up", END)
```

## Retries with backoff

Third failure: the network. Sometimes the problem is not your code at all.

Some failures are transient. The provider says you are sending too many requests, or the server is overloaded, or the network times out. Waiting and retrying usually works, like redialling when a call drops. Others are permanent, like a bad argument. Retrying those just wastes time. They go back to the model as errors.

**Retry it, or report it?**

- **Transient: retry**
  - Rate limit (HTTP 429)
  - Server overloaded (HTTP 5xx)
  - Network timeout
- **Permanent: report**
  - Bad argument
  - A date with no data
  - Send back to the model as an error

Retry with exponential backoff: wait one second, then two, then four, doubling each time. Add a small random amount, called jitter, so thousands of clients do not all retry at the same instant. With three retries, the worst case is seven seconds of waiting before you give up.

**Wait longer each time, plus a little jitter**

- Retry 1: 1 s
- Retry 2: 2 s
- Retry 3: 4 s

*Worst case: 1 + 2 + 4 = 7 seconds of waiting, then give up.*

Put retries for model calls in one place, the adapter that talks to the provider, so every caller gets them. Put tool retries inside tools that call the network. And only retry operations that are safe to repeat. The word for that is idempotent. Reading a ranking twice is harmless. Sending a UPI payment twice is not.

**Where retries belong**

- Model-call retries: in the adapter, so every caller gets them
- Tool retries: in the tool, for tools that call the network
- Only retry what is safe to repeat (idempotent)

*Reading a ranking twice is harmless. Sending a UPI payment twice is not.*

## Parallel tool calls

Last one: speed. A model can ask for several tools in a single reply.

Rahul asks: explain NAV and expense ratio. NAV, or net asset value, is the price of one unit of a fund. The model asks for two definitions in one reply, with two ids, call A and call B. The rule: run them all, and return all the results in one message, each tagged with its own id. The ids match answers to requests, so order does not matter.

**“Explain NAV and expense ratio”**

> **User:** Explain NAV and expense ratio.
>
> **Assistant:** [tool_use id=call_a] lookup_definition("NAV")   [tool_use id=call_b] lookup_definition("expense ratio")
>
> **Tool:** [tool_result call_a] ...   [tool_result call_b] ...

Our simple tools node runs calls one after another. If three slow calls take point eight, one point two and point five seconds, that is two and a half seconds in total. Run them at the same time, and it takes about as long as the slowest one, one point two seconds.

**Sequential vs concurrent**

- Sequential: 2.5 s
- Concurrent: 1.2 s

*Concurrent takes about as long as the slowest call.*

Here is how, with a thread pool from Python's standard library. Each call runs in its own worker, and the same error handling applies. Only do this for calls that do not depend on each other. If the second call needs the first one's output, the model will ask for them in separate rounds, and it should.

**A thread pool in the tools node**

`day03_agents/agent.py`
```python
from concurrent.futures import ThreadPoolExecutor

def run_one(call):
    fn = TOOL_FUNCS.get(call["name"])
    try:
        result = fn(**call["input"]) if fn else {"error": "unknown tool"}
    except Exception as exc:
        result = {"error": f"{type(exc).__name__}: {exc}"}
    return {"type": "tool_result", "tool_use_id": call["id"],
            "content": json.dumps(result)}

with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(run_one, state["pending_calls"]))
```

Quick check. Pause and answer. A tool throws an exception. What must the agent do, and what two things must it never do? The answer: return the error to the model as a clearly labelled result. Never let it crash the whole request. And never swallow it into an empty result that the model might fill with a made up answer.

**Quick check:** A tool fails. Name one thing the agent must do, and two things it must never do.

<details><summary>Answer</summary>

Return the error as a result. Never let it crash the request, never return an empty result.

</details>

Let's recap. Tool errors go back to the model as results, never crashes. Write error messages the model can act on. Always cap the rounds, and close open calls when you stop. Retry only transient failures that are safe to repeat, with backoff. And run independent tool calls at the same time. Next: the agent patterns every interviewer expects you to name.

- Tool errors go back to the model as results, never crashes
- Write error messages the model can act on
- Always cap tool rounds; close open calls when you stop
- Retry only transient, safe-to-repeat failures, with backoff
- Run independent tool calls at the same time

The code is in the day three agents folder, linked in the description. Try asking it about a weekend date and see what it says. See you in the next part.

---

← [Day 3, Part 3](day03_p3.md) · [All lessons](README.md) · [Day 3, Part 5](day03_p5.md) →
