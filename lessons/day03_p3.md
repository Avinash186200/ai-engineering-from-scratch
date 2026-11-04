# Day 3, Part 3: LangGraph Memory: Threads, Checkpoints and Human-in-the-Loop

**Watch:** [youtu.be/ADLYwHTLEXY](https://youtu.be/ADLYwHTLEXY) · **Code:** [`day03_agents/`](../day03_agents/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

How does an AI agent remember a conversation, survive a server restart, and pause for a human's approval? In this episode we run our research assistant's LangGraph agent and look inside its saved state.

## What you will learn

- invoke() and thread_id: one turn of one conversation
- How two users are kept completely separate
- Checkpointers: MemorySaver, SQLite and Postgres
- Reading saved state with get_state and get_state_history
- Interrupts: pausing for human approval, and the side-effect trap
- Streaming progress to the user

## Chapters

- [0:00](https://youtu.be/ADLYwHTLEXY?t=0) Intro
- [0:28](https://youtu.be/ADLYwHTLEXY?t=28) invoke() and thread_id
- [1:22](https://youtu.be/ADLYwHTLEXY?t=82) Two users, kept apart
- [2:16](https://youtu.be/ADLYwHTLEXY?t=136) Checkpointers: saving after every step
- [3:41](https://youtu.be/ADLYwHTLEXY?t=221) Inside the saved snapshots
- [5:17](https://youtu.be/ADLYwHTLEXY?t=317) Human in the loop: interrupts
- [7:36](https://youtu.be/ADLYwHTLEXY?t=456) Streaming progress

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In part two, we built our agent as a graph: two nodes, a shared state, and edges between them. Now we run it, and see how it remembers conversations, survives restarts, and waits for a human.

As always, the code is in the day three agents folder, and you can watch at one point two five times speed.

## invoke() and thread_id

Let's start with how you actually run the graph: a method called invoke.

Here is a small helper called ask. It runs one turn of one conversation. The key line is the config, which carries a thread id. A thread is one conversation, and the thread id is its name, just a string you choose, like priya one.

**The ask() helper**

`day03_agents/agent.py`
```python
def ask(app, question: str, thread_id: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(
        {"messages": [{"role": "user", "content": question}],
         "pending_calls": [], "tool_rounds": 0},
        config=config,
    )
    return {"answer": final_text(result["messages"])}

ask(app, "Which funds look best on 2025-06-20?", thread_id="priya-1")
```

Invoke does five things. It reads the thread id. It loads the latest saved state for that thread; for a new thread there is none. It merges your input using the reducers, so the question is appended. It runs the nodes, saving after every step. And it returns the final state when it reaches end.

**What invoke() does**

1. Reads the thread_id from the config
2. Loads the latest saved state for that thread (none if new)
3. Merges your input using the reducers
4. Runs nodes along the edges, saving after each step
5. Returns the final state when it reaches END

When you run agent dot py, it asks three questions on the thread priya one. Each simple question makes four messages, so the thread holds twelve. Then it checks a thread called rahul one, which was never used. It holds zero. Same thread id, the conversation continues. New thread id, it starts fresh.

**Three questions on one thread**

- priya-1: 12 messages
- rahul-1: 0 messages

*Same thread id: it continues. New thread id: it starts fresh.*

A common and dangerous mistake: using one fixed thread id, like the word default, for everyone. Then every user appends to one shared conversation and can see each other's questions. The thread id must come from your server, from the logged in session, never from anything the user or the model can type.

**Where the thread id comes from**

> **Never one fixed id like “default” for everyone.**
> Then every user appends to one conversation and sees the others. Derive it on the server from the logged-in session, never from text a user or model can set.

## Checkpointers: saving after every step

So where is that state actually stored? In something called a checkpointer.

A checkpointer saves a snapshot of the full state after every step, filed under the thread id and a unique checkpoint id. Think of the auto save in a video game: if the power goes, you restart from the last save point, not from the beginning. It gives you memory, restart safety, and an audit trail.

**A checkpointer**

- Saves a snapshot of the full state after every step
- Keyed by thread id, plus a unique checkpoint id
- Gives you memory, restart safety and an audit trail

There are three common choices. MemorySaver keeps state in a Python dictionary, which vanishes on restart, so it is for tests and demos. SQLite saver uses a local file, fine on one machine. Postgres saver uses a real database shared by all your servers, which is what production uses. They share one interface, so swapping is one line.

**MemorySaver, SQLite, Postgres**

| Checkpointer | Where state lives | Survives restart? |
|---|---|---|
| MemorySaver | A Python dict in memory | No: tests, demos |
| SqliteSaver | A local SQLite file | Yes, on one machine |
| PostgresSaver | PostgreSQL tables | Yes, shared by all servers |

*Same interface: swapping is a one-line change.*

Here is the production version. Same build app, same ask, just a different saver. Notice the database address comes from configuration, never typed into the code, because it usually contains a password. You need a separate package for this, langgraph checkpoint postgres.

**Swapping in Postgres**

`illustrative`
```python
from langgraph.checkpoint.postgres import PostgresSaver

with PostgresSaver.from_conn_string(DB_URI) as saver:   # from config, never hard-coded
    saver.setup()                  # creates the tables on first use
    app = build_app(llm, checkpointer=saver)
    ask(app, "Which funds look best on 2025-06-20?", thread_id="priya-1")
```

Let's see the snapshots for one question: what is an expense ratio? Before anything runs, there is a snapshot of the raw input. Then step zero: the question is added, and the next node is llm.

Step one: the model asked for a tool, so next is tools. Step two: the tool result is added, back to llm. Step three: the final answer, and nothing is next. Here is the power of this. If the server crashed right after step one, the saved state still says, next is tools, with the request saved, so it can continue from there.

**One question, five snapshots**

| Snapshot | Next node | Msgs | What happened |
|---|---|---|---|
| step -1 | __start__ | 0 | the raw input |
| step 0 | llm | 1 | question added |
| step 1 | tools | 2 | model asked for a tool |
| step 2 | llm | 3 | tool result added |
| step 3 | (done) | 4 | final answer |

*If the server dies after step 1, the saved state still says: next = tools.*

You can read the saved state without running anything. Get state gives the latest snapshot: its values, and what runs next. An empty next means finished. Get state history gives every snapshot, newest first. So when someone asks, why did the agent say that last Tuesday, you can replay every step.

**get_state and get_state_history**

`day03_agents/agent.py`
```python
cfg = {"configurable": {"thread_id": "priya-1"}}
snap = app.get_state(cfg)        # latest snapshot for this thread
snap.values                      # the State dict
snap.next                        # () means finished
list(app.get_state_history(cfg)) # every snapshot, newest first
app.update_state(cfg, {...})     # a human corrects a value
```

If you have trained models before: a checkpointer is like saving a checkpoint every epoch, so a crash at epoch thirty seven resumes from thirty seven. And a thread id is like an experiment tracking run id: everything from one conversation is filed under it, and nothing else.

**The same ideas you may already know**

| Machine learning | LangGraph |
|---|---|
| Saving a checkpoint every epoch | Saving state after every step |
| An experiment-tracking run id | A thread id |

## Human in the loop: interrupts

Now, what if an action must not happen without a person saying yes? For that, LangGraph has interrupts.

An interrupt pauses the graph at a defined point, saves the state through the checkpointer, and hands control back to your application, so you can ask a human. Later, even hours later, on a different server, you resume from that checkpoint. That is why it only works with a checkpointer: the paused state has to live somewhere.

**An interrupt**

- Pauses the graph at a defined point
- Saves the state through the checkpointer
- Hands control back to your app, to ask a human
- Resume later, even hours later, on a different server

The simplest style is a breakpoint. Compile with interrupt before tools. Now the graph stops before running any tool. A reviewer can see exactly which tool the model wants, with which arguments, before anything happens. To carry on, invoke again with none as the input, which means, continue this thread.

**A breakpoint before a node**

`day03_agents/agent.py`
```python
app = g.compile(checkpointer=MemorySaver(), interrupt_before=["tools"])
app.invoke(first_input, cfg)

app.get_state(cfg).next                    # ('tools',)  paused
app.get_state(cfg).values["pending_calls"]
# [{'id': 'call_1', 'name': 'rank_funds',
#   'input': {'as_of': '2025-06-20', 'top_n': 3}}]

app.invoke(None, cfg)                      # None = carry on
```

The second style is an interrupt inside a node. The node calls interrupt with a question for the human, say, invest fifty thousand rupees in Bharat Growth Fund? The graph pauses. When the human answers, you resume with a command carrying their answer, and interrupt returns that answer inside the node.

**An interrupt inside a node**

`illustrative`
```python
from langgraph.types import interrupt, Command

def approve(state):
    decision = interrupt({"question": "Invest ₹50,000 in Bharat Growth Fund?"})
    return {"status": "approved" if decision == "yes" else "rejected"}

r = app.invoke(start, cfg)              # pauses; payload shown to a human
r = app.invoke(Command(resume="yes"), cfg)   # the human said yes
```

Here is the trap that catches people. When you resume, the interrupted node runs again from its very first line. So if you sent the order before calling interrupt, it gets sent twice. Never put a side effect before interrupt in the same node. Put the real action in the next node.

**The node runs again on resume**

> **Never put a side effect before interrupt() in the same node.**
> On resume, the node restarts from its first line. Put the real action, like sending the order, in the next node.

So a good design looks like this. The agent proposes an action. An approval node interrupts and shows the exact action. The human's identity is checked on the server. And a separate execute node runs only on yes. The approval is part of the structure, not just a polite request in the prompt that the model might ignore.

**Approval before money moves**

**Agent** (proposes the action) → **Approval node** (interrupt: show the exact action) → **Human** (identity checked on the server) → **Execute node** (runs only on yes; safe to retry)

*Make approval structural, not a line in the prompt.*

## Streaming progress

One last feature. Invoke only returns when the whole run is finished. For a user waiting on three rounds, that can feel like a long silence.

Stream runs the same graph, but hands you events as they happen. Values gives the full state after each step, good for debugging. Updates gives just what each node returned, good for a progress line like, looking up rankings. Messages gives model tokens as they arrive, for a typing effect. And custom lets a node send anything you like.

**Four stream modes**

| Mode | Each event contains | Use |
|---|---|---|
| values | The full state after each step | Debugging |
| updates | What each node returned | “Looking up rankings…” |
| messages | Model tokens as they arrive | Typing effect |
| custom | Anything a node sends | Your own progress |

With updates mode, the expense ratio question produces three events: the llm node, then the tools node, then the llm node again. Each one tells you which fields changed. That is enough to show the user what the agent is doing, step by step.

**stream_mode="updates"**

`terminal`
```python
for event in app.stream(inp, cfg, stream_mode="updates"):
    print(event.keys())

# UPDATE from llm   -> ['messages', 'pending_calls']
# UPDATE from tools -> ['messages', 'pending_calls', 'tools_called', 'tool_rounds']
# UPDATE from llm   -> ['messages', 'pending_calls']
```

Quick check. Pause and answer. Your server restarts in the middle of Priya's conversation. With MemorySaver, what happens? And with Postgres saver? The answer: with MemorySaver, the state lived in the process, so it is gone. With Postgres, the same thread id loads the last snapshot, and the conversation carries on.

**Quick check:** Our server restarts mid-conversation. With MemorySaver, what happens? With PostgresSaver?

<details><summary>Answer</summary>

MemorySaver: the conversation is lost. PostgresSaver: it resumes from the last saved step.

</details>

Let's recap. Invoke runs one turn, and the thread id picks the conversation. Thread ids come from the server, never from user text. A checkpointer saves state after every step, and production uses Postgres. Interrupts pause for a human, and side effects go in the next node. And stream shows progress. Next: what to do when things go wrong.

- invoke() runs one turn; thread_id picks the conversation
- Thread ids come from the server session, never from user text
- A checkpointer saves state after every step: Postgres in production
- Interrupts pause for a human; side effects go in the next node
- stream() shows progress while the agent works

Try it yourself: run python day03 agents slash agent dot py and look at the message counts at the end. Link in the description. See you in the next part.

---

← [Day 3, Part 2](day03_p2.md) · [All lessons](README.md) · [Day 3, Part 4](day03_p4.md) →
