# Day 3, Part 2: LangGraph Explained: Nodes, State, Reducers and Edges

**Watch:** [youtu.be/ot2NK7-Oh0Q](https://youtu.be/ot2NK7-Oh0Q) · **Code:** [`day03_agents/`](../day03_agents/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

LangGraph turns the agent loop into a graph you can see, test and save. In this episode we build our research assistant's agent from its parts, one primitive at a time.

## What you will learn

- What a node is (one function, one job) and why it is NOT a box of tools
- State: the shared whiteboard every node reads and writes
- Reducers: why chat history disappears without one
- Normal edges, conditional edges, START and END
- compile(): from a blueprint to a runnable app, and why a graph beats a while-loop

## Chapters

- [0:00](https://youtu.be/ot2NK7-Oh0Q?t=0) Intro
- [1:19](https://youtu.be/ot2NK7-Oh0Q?t=79) A node: one function, one job
- [2:58](https://youtu.be/ot2NK7-Oh0Q?t=178) State: the shared whiteboard
- [3:56](https://youtu.be/ot2NK7-Oh0Q?t=236) Reducers: how updates are merged
- [4:29](https://youtu.be/ot2NK7-Oh0Q?t=269) What breaks without a reducer
- [6:03](https://youtu.be/ot2NK7-Oh0Q?t=363) Edges, START and END
- [7:28](https://youtu.be/ot2NK7-Oh0Q?t=448) compile(), and why a graph at all

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In part one, we saw that every agent is one small loop: call the model, run the tools it asks for, add the results, repeat. Today we turn that loop into a graph, using a library called LangGraph.

Open day three agents, agent dot py, next to this video if you can. Everything we discuss is in that file.

LangGraph is an open source Python library for building multi step language model applications as graphs. A graph here just means boxes connected by arrows. LangGraph does not call models itself. It gives you the structure around them: shared state, steps, saving, pausing, and streaming.

**LangGraph in one sentence**

- An open-source Python library for multi-step LLM apps, built as graphs
- It does not call models itself: you put model calls inside nodes
- It gives the structure: shared state, steps, saving, pausing, streaming

Here is our whole agent as a graph. Start goes to the llm node, which asks the model. If the model requested tools, we go to the tools node, which runs them, and then always back to the llm node. When the model answers in text, we go to end. Two nodes and one decision.

**The loop as a two-node graph**

**START** (the entry point) → **llm node** (ask the model) → **tools node** (run requested tools) → **END** (answer ready)

*llm → tools → back to llm, until the model answers.*

*Two nodes, one decision: after the model, run tools or finish?*

## A node: one function, one job

Let's take each piece in turn, starting with the node.

A node is just a plain Python function that you register in the graph under a name. LangGraph calls it with the current state. It returns a dictionary containing only the fields it wants to change. We call that a partial update. That is all a node is.

**A node is a plain Python function**

`day03_agents/agent.py`
```python
def llm_node(state: State) -> dict:        # reads the whole state
    out = llm.complete(SYSTEM, state["messages"], TOOLS)
    ...
    return {"messages": [reply],                # returns only
            "pending_calls": out["tool_calls"]} # what changed

g.add_node("llm", llm_node)    # register it under the name "llm"
```

Here is where most beginners get confused. It is tempting to picture the tools node as a box containing three tools. Picture it instead as one function with one job: run whatever tool calls are pending. The tools themselves are ordinary Python functions in a lookup table. You could add ten more tools tomorrow without touching the graph at all.

**Is the tools node a box of tools?**

> **No. It is one function with one job: run whatever tool calls are pending.**
> The tools are ordinary functions in a lookup table. Add ten more tomorrow without touching the graph.

Side by side. A node is a step in the graph, seen only by you and LangGraph; the model never knows nodes exist. A tool is a function described to the model, and the model asks for it. Think of a node as a step in a recipe, and a tool as a kitchen instrument that step can use.

**Node versus tool**

|  | Node | Tool |
|---|---|---|
| What it is | A step in the graph | A function described to the model |
| Who sees it | Only you and LangGraph | The model sees its description |
| Who decides it runs | The graph's arrows (code) | The model asks for it |
| Examples | llm, tools | rank_funds, lookup_definition |

*Analogy: a node is a step in a recipe; a tool is an instrument it can use.*

A rule of thumb. A good node does one thing you can describe in one sentence and test on its own: call the model, run the pending tools, ask a human to approve. If you cannot name its job in one sentence, split it into two nodes.

**A good node**

> **If you cannot name a node's job in one sentence, split it.**
> Call the model. Run the pending tools. Ask a human to approve. Each is testable on its own.

## State: the shared whiteboard

Next: the state. This is where the agent keeps everything it knows.

The state is a dictionary that every node reads from and writes to, like a shared whiteboard in an office. We declare its shape with a TypedDict, a standard Python way of saying, a dictionary with these keys of these types. Messages is the conversation the model sees.

Pending calls is the hand over from the llm node to the tools node. Tools called is a log, handy for tests. And tool rounds is a counter for our loop limit. Notice that nodes never pass data to each other directly. The llm node writes pending calls; the tools node reads it. So every value can be inspected, and saved.

**Declaring the state with TypedDict**

`day03_agents/agent.py`
```python
class State(TypedDict):
    messages: Annotated[list[dict], append]   # history: added to
    pending_calls: list[dict]                 # tool calls just requested
    tools_called: Annotated[list[str], append]
    tool_rounds: int                          # counter for the limit
```

*Nodes never pass data directly. If it matters, it is in the state.*

## Reducers: how updates are merged

Now a small detail that causes big bugs: reducers.

When a node returns a new message, LangGraph must decide how to combine it with the messages already there. The rule is the field's reducer. By default there is no reducer, so the update simply overwrites. That is right for the round counter. For messages, we attach an append reducer, so new messages are added to the end.

**Overwrite or append?**

- **No reducer (default)**
  - The update replaces the old value
  - Right for pending_calls and tool_rounds
  - Only the latest value matters
- **With a reducer**
  - Attach with Annotated[list, append]
  - append(a, b) returns a + b
  - Right for messages: history grows

Here is what happens without the reducer. A tiny graph with one node that replies hi, called twice on the same conversation. After turn two, the list holds only one message. The question was overwritten by the reply, and turn one by turn two. The model would not even see the question.

With the append reducer, after turn two you get the full history, in order: question one, reply, question two, reply. So forgetting the reducer on your history field means your agent has no memory at all.

**Two turns on the same conversation**

| Setup | messages after turn 2 |
|---|---|
| No reducer | [assistant: hi]   (everything else gone) |
| Annotated[list, append] | [user q1, assistant hi, user q2, assistant hi] |

*Forget the reducer on history, and your agent has no memory.*

A subtle bonus: reducers also apply to the input you send in. So you can pass just the new question, and it lands at the end of the saved conversation. Meanwhile, tool rounds set to zero has no reducer, so it overwrites, and each new question starts with a fresh counter. LangGraph also ships a ready made one called add messages.

**Reducers apply to your input too**

- Pass only the new question: it lands at the end of the history
- Pass tool_rounds: 0 with it: no reducer, so it resets
- So the loop limit is per question, not per conversation
- LangGraph also ships add_messages, a ready-made message reducer

If you know pandas, here is the comparison. An append reducer is like pandas concat: you add new rows to the table. No reducer is like assigning new rows to the variable: the old table is gone. Forgetting the reducer is like overwriting your whole dataset with the latest batch.

**The same idea in pandas**

| pandas | LangGraph |
|---|---|
| df = pd.concat([df, new_rows]) | Field with an append reducer |
| df = new_rows | Field with no reducer |

## Edges, START and END

We have nodes and state. Now, the arrows between nodes. In LangGraph, they are called edges.

There are two kinds. A normal edge is fixed: after A, always B. After the tools run, we always go back to the model, because it must see the results. A conditional edge calls a function that reads the state and returns the name of the next node. After the model, go to tools, or finish.

**A guarantee, or a decision**

- **Normal edge**
  - Fixed: after A, always B
  - tools → llm, always
  - The model must see the results
- **Conditional edge**
  - A function reads the state
  - Returns the name of the next node
  - llm → tools, or llm → END

*A normal edge is a guarantee. A conditional edge is a decision.*

Here is the wiring. The route function says: if the model asked for tools, and we have used fewer than five rounds, go to tools. Otherwise, go to end. That five is our safety limit. Start and end are two special names: the virtual entry and exit of the graph. Because route is plain Python, you can test it without any model at all.

**Two nodes, three edges**

`day03_agents/agent.py`
```python
def route(state: State) -> str:
    if state["pending_calls"] and state.get("tool_rounds", 0) < 5:
        return "tools"
    return END

g = StateGraph(State)
g.add_node("llm", llm_node)
g.add_node("tools", tool_node)
g.add_edge(START, "llm")                                  # entry
g.add_conditional_edges("llm", route, {"tools": "tools", END: END})
g.add_edge("tools", "llm")                                # always back
app = g.compile(checkpointer=MemorySaver())
```

The third argument to add conditional edges is called the path map. It lists the allowed answers from the routing function, and which node each one leads to. It documents the branches, and lets LangGraph check and draw your graph.

**The path map**

- Third argument: {"tools": "tools", END: END}
- Lists the allowed answers from route, and where each one leads
- LangGraph uses it to validate and draw the graph

## compile(), and why a graph at all

Finally, the last line of that code: compile. And a fair question: why bother with a graph at all?

Adding nodes and edges only builds a blueprint. Nothing can run yet. Compile does three things. It validates the structure, so mistakes surface now, not halfway through a user's request. It freezes the graph into a runnable app. And it attaches options, like the checkpointer that saves state, which we cover in the next part.

**What compile() does**

1. Validates: every edge points to a real node, there is an entry point
2. Freezes it into a runnable app: invoke, stream, get_state
3. Attaches options: the checkpointer, and pause points

*Before compile: a drawing of a house. After: a house you can live in.*

You could write the loop as twenty lines of while true, and many people do. So what does the graph add? You can test each step on its own. And you can survive a server restart just by attaching a checkpointer.

You can resume a conversation tomorrow with the same thread id. You can pause for a human to approve, then resume. And you can show progress while it runs. Each of these is weeks of work in a hand written loop.

**What the graph gives you for free**

| Need | Hand-written loop | LangGraph |
|---|---|---|
| Test each step | Tangled in one function | Each node testable |
| Survive a restart | Build it yourself | Attach a checkpointer |
| Resume tomorrow | Your own session store | Same thread id |
| Pause for a human | A job queue + state machine | interrupt, then resume |
| Show progress | Callbacks you design | stream() |

If you have used data pipelines, like a scikit learn pipeline or an Airflow job, a state graph is a pipeline with two extra powers. It can branch based on intermediate results, and it can loop back to an earlier step. And an agent is, by nature, a loop: model, tools, model.

**A pipeline that can branch and loop**

> **A state graph = a pipeline with two extra powers.**
> Branching on intermediate results, and cycles. An agent is a cycle: model → tools → model.

Quick check. Pause and answer. You want the agent to also check fund fees. Do you add a new node, or a new tool? The answer: a new tool. You write the function, its description and schema, and add it to the lookup table. The graph does not change at all. A new capability for the model is a tool, not a node.

**Quick check:** You want the agent to also check fund fees. Do you add a new node or a new tool?

<details><summary>Answer</summary>

A new tool: a function, its description and schema, and a lookup entry. The graph does not change.

</details>

Let's recap. A node is one function with one job. The tools node just runs pending calls; the tools are plain functions. State is the shared whiteboard, and reducers decide whether updates overwrite or append. Normal edges are guarantees, conditional edges are decisions. And compile turns the blueprint into an app. Next: how the agent remembers, with thread ids and checkpoints.

- A node is one function with one job; it returns only what changed
- The tools node runs pending calls; tools are plain functions
- State is the shared whiteboard; reducers decide overwrite vs append
- Normal edges are guarantees; conditional edges are decisions
- compile() validates the graph and makes it runnable

Run python day03 agents slash agent dot py to see this graph answer questions. The link is in the description. See you in the next part.

---

← [Day 3, Part 1](day03_p1.md) · [All lessons](README.md) · [Day 3, Part 3](day03_p3.md) →
