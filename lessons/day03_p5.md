# Day 3, Part 5: AI Agent Patterns: ReAct, Router, Supervisor, Memory

**Watch:** [youtu.be/DqlT5qv-MoY](https://youtu.be/DqlT5qv-MoY) · **Code:** [`day03_agents/`](../day03_agents/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

The agent patterns every AI engineering interviewer expects you to name, plus how agents handle memory across long conversations. We finish by walking one analyst's full session through our research assistant.

## What you will learn

- ReAct, router, supervisor/worker, reflection and plan-and-execute, with small examples
- When each pattern is worth its cost
- Short-term (thread) memory vs long-term memory
- Trimming and summarising long conversations safely
- One complete session, end to end, and a hands-on exercise: add a fourth tool

## Chapters

- [0:00](https://youtu.be/DqlT5qv-MoY?t=0) Intro
- [0:26](https://youtu.be/DqlT5qv-MoY?t=26) Five patterns you should name
- [3:26](https://youtu.be/DqlT5qv-MoY?t=206) Memory: short-term and long-term
- [4:25](https://youtu.be/DqlT5qv-MoY?t=265) Trimming long conversations
- [6:00](https://youtu.be/DqlT5qv-MoY?t=360) One session, end to end

## Lesson notes

Slide content and the full narration, in order.

Welcome back to the last part of day three. In part four, we made our agent fail safely: errors as results, a round limit, retries, and parallel calls. Now we zoom out, to the common shapes agents take, and how they remember things.

As always, watch at one point two five times speed if you like.

## Five patterns you should name

Patterns are just names for shapes of graph. Interviewers use them as shorthand, so you should be able to draw each one, and say when it is worth the cost.

Pattern one is ReAct, short for reason and act, from a twenty twenty two research paper. Think, call a tool, read the result, think again. Say Priya asks, do both ranking models agree on the top fund? The agent ranks with one model, then the other, then answers. The loop from part one is ReAct. Our assistant is a ReAct agent.

**Reason, act, observe, repeat**

1. Thought: I need the ranking from the first model
2. Action: rank_funds(as_of="2025-06-20")  →  #1 Bharat Growth Fund
3. Thought: now the second model. Action: rank_funds(..., model="ridge")
4. Answer: no, the two models disagree on the top fund

Pattern two is the router. It classifies the request once, then sends it down one specialised path, each of which can be a simple workflow. It is cheaper and more predictable than a full agent. The catch: if the router gets the label wrong, the request goes to a path that cannot answer it.

**Classify once, then dispatch**

`illustrative`
```python
def classify(state):                  # one cheap model call, or keywords
    return {"intent": llm_label(state["question"],
                                labels=["ranking", "definition", "document"])}

g.add_conditional_edges("classify", lambda s: s["intent"],
    {"ranking": "ranking_flow", "definition": "glossary_flow",
     "document": "doc_flow"})
```

Pattern three is supervisor and workers. A supervisor agent splits the task, and hands each piece to a worker agent with its own prompt and tools. For a briefing on the top funds, a ranking worker gets the numbers, a research worker summarises documents, and the supervisor combines them. It is worth it only when one context would overflow. Otherwise it multiplies cost and failure points.

**Delegate, then combine**

**Supervisor** (“Brief me on the top funds”) → **Ranking worker** (top 5 funds with numbers) → **Research worker** (summarises fund documents) → **Supervisor** (writes the briefing)

*Worth it when one context would overflow, or tasks need different tools.*

Pattern four is reflection. A critic reviews the draft before it goes out. Rule: every number must appear in a tool result. The draft says six percent a year, but no tool said that, so it goes back, and the revision drops it. The nice part: this check can be plain code that extracts numbers and compares them. Cheaper and more reliable than another model.

**A critic checks the draft**

1. Rule: every number in the answer must appear in a tool result
2. Draft: “Bharat Growth Fund: +0.53%, roughly 6% a year”
3. Critic: “6% a year” is in no tool result. Send it back.
4. Revised draft drops the made-up figure

*Part of the critic can be plain code: cheaper and more reliable.*

Pattern five is plan and execute. The model writes the full plan up front, then the steps run, often with a cheaper model or plain code, and it re-plans only if something fails. Compared with ReAct, fewer expensive calls, and the plan is visible for review. But it adapts less well when early results should change the plan.

**Plan everything first, then run it**

1. Plan: 1. rank with model A  2. rank with model B
2. 3. look up the fund details  4. write the comparison
3. Execute the steps, often with a cheaper model or plain code
4. Re-plan only if a step fails

One interview tip. Patterns are vocabulary. Don't claim a system uses all five. Say which one fits, and why. For our research assistant: a tool calling agent in the ReAct family, with a fixed set of tools, and saved state.

**Patterns are vocabulary**

> **Say which pattern fits, and why.**
> Not that a system uses all of them. Each one adds cost; name the cheapest that does the job.

## Memory: short-term and long-term

Now, memory. Agents have two very different kinds.

Short term memory is the thread: this conversation, saved automatically by the checkpointer after every step. Long term memory holds facts that should outlive a conversation, like, Priya prefers debt funds. It lives across threads, usually per user, and a node saves it on purpose, when it decides something is worth keeping.

**Thread memory vs long-term memory**

|  | Short-term (thread) | Long-term (store) |
|---|---|---|
| Holds | This conversation | Facts that outlive it |
| Scope | One thread id | Across threads, per user |
| Saved by | Checkpointer, every step | A node that chooses to |
| Example | “She asked about 20 June” | “Priya prefers debt funds” |

In LangGraph, long term memory is a store: a simple key value memory, with namespaces, here Priya's preferences. You pass it to compile, next to the checkpointer, and any node can read it, say, to rank debt funds first for Priya. In production, the store would be backed by a database, just like the checkpointer.

**The store: a key-value memory**

`illustrative`
```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
store.put(("priya", "prefs"), "style", {"fund_type": "debt"})
store.get(("priya", "prefs"), "style").value
# -> {'fund_type': 'debt'}

app = g.compile(checkpointer=saver, store=store)
```

Thread memory has a cost. Every model call resends the whole message list, and the context window, the amount of text a model can read at once, is limited, as we saw on day one. Big tool results make threads grow fast. There are two fixes: trimming, and summarising.

**Long threads get expensive**

- Every model call resends the whole message list
- The context window is finite (Day 1)
- Big tool results make threads grow fast

*Two fixes: trim what you send, or summarise the old part.*

Trimming sends the model only recent turns. One rule matters above all: never cut between a tool request and its result, because half a pair gets rejected. The safe cut point is the start of a real question, a user message with plain text. On our twelve message thread, keeping two turns sends the last eight messages.

**Cut only at the start of a real question**

`day03_agents/agent.py`
```python
def trim_for_model(messages, keep_turns=2):
    starts = [i for i, m in enumerate(messages)
              if m["role"] == "user" and isinstance(m["content"], str)]
    if len(starts) <= keep_turns:
        return messages
    return messages[starts[-keep_turns]:]

# in llm_node:
out = llm.complete(SYSTEM, trim_for_model(state["messages"]), TOOLS)
```

*Never cut between a tool request and its result.*

Summarising keeps more meaning. When the thread gets long, a model call condenses the older turns into a short summary, and recent turns are kept word for word. Illustrative numbers: forty turns of fifteen hundred tokens is sixty thousand tokens per call. The last ten turns plus a five hundred token summary is fifteen and a half thousand. About a quarter.

**40 turns: full history vs summary**

- Full history: 60,000 tokens
- Summary + last 10: 15,500 tokens

*About a quarter of the tokens, and the old context survives.*

The key idea: trim the view, not the record. Keep the full history in the saved state, for audit and replay, and trim only what you send to the model, inside the llm node.

**Trim the view, not the record**

> **Keep the full history saved. Trim only what the model sees.**
> The full record is your audit trail and replay. Trimming happens inside the llm node.

## One session, end to end

Let's put the whole day together, with one analyst's session through our research assistant.

Priya logs in, and the server, not Priya, decides her thread id. She asks which funds look best on twentieth June. Invoke loads her thread, the reducer appends the question, and the model asks for the ranking tool. The tool computes the numbers, the result goes back with the matching id, and the model explains. No number came from its memory.

She asks, and the next day? The thread remembers she means June, and a ranking. But the twenty first is a Saturday, so the tool returns an error, and the model says so plainly. Overnight, the server restarts. Nothing is lost, because the state lives in Postgres. Next morning, same thread, same context. And if anyone asks why it answered that way, the saved history shows every step.

**Every idea from today, in one session**

1. Priya logs in: the server picks her thread id
2. “Which funds look best on 2025-06-20?” → model asks for rank_funds
3. The tool ranks; the model explains. No number from its memory.
4. “And the next day?” Saturday: the tool returns an error; the model says so
5. Overnight restart; next morning, same thread, same context

*Later, an audit: the saved history shows every step.*

Now your exercise. Add a fourth tool called compare models, which shows the top funds from both ranking models side by side. It touches four places: the function, its schema, the lookup table, and, for the fake model in agent dot py, a keyword route. Then run python day03 agents slash agent dot py. Notice what you did not touch: the graph.

**Exercise: add a fourth tool, compare_models**

1. Write the function: top funds from both models, side by side
2. Write its schema: what it does, when to use it, constraints
3. Add it to TOOL_FUNCS, the lookup table
4. Teach the FakeLLM a keyword route for “compare”

*What you did not touch: the graph.*

Two more experiments. Change the round limit from five to two, and run again. The output does not change, because every demo question needs only one round. The limit is insurance, not normal behaviour. And if you have an API key, run with dash dash real, and ask, do the two models agree? The keyword fake misroutes it. A real model reads the descriptions, and should pick the right tool.

**Two more experiments**

- Change the round limit from 5 to 2. Does the output change? Why not?
- Optional: run with a real model and an API key, using --real
- Ask “Do the two models agree?” The fake misroutes; a real model shouldn't

Final quick check for the day. Pause and answer. When is the supervisor and worker pattern worth its cost? The answer: when one context would overflow, or when subtasks need different tools or models. Otherwise, it just multiplies cost, delay, and the places things can fail.

**Quick check:** When is the supervisor/worker pattern worth its cost?

<details><summary>Answer</summary>

When one context would overflow, or subtasks need different tools or models. Otherwise it adds cost and failures.

</details>

Let's recap day three's final part. ReAct is think, act, observe, and our assistant is a ReAct agent. Router, supervisor, reflection, and plan and execute are vocabulary: name the cheapest one that fits. Thread memory is automatic; long term memory is a store. Trim only at real question boundaries, and trim the view, not the record. Tomorrow, on day four: MCP, a standard way to plug our tools into any AI.

- ReAct: think, act, observe; our assistant is a ReAct agent
- Router, supervisor, reflection, plan-and-execute: name the cheapest fit
- Thread memory is automatic; long-term memory is a store
- Trim at real question boundaries; trim the view, not the record
- A new capability is a new tool, not a new node

That is day three done. The code is in the description. If this helped, subscribe, and I will see you on day four.

---

← [Day 3, Part 4](day03_p4.md) · [All lessons](README.md) · [Day 4, Part 1](day04_p1.md) →
