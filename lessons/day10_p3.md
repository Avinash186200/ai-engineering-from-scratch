# Day 10, Part 3: AI Engineer Coding Interview: LangGraph Agent + NumPy Retrieval

**Watch:** [youtu.be/YsTsbze0Glo](https://youtu.be/YsTsbze0Glo) · **Code:** [`day10_mock/`](../day10_mock/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

The coding round of our mock interview: two 20-minute tasks from a blank file, walked through line by line.

## What you will learn

- Part 1: a LangGraph agent with one tool, a fake LLM router, a conditional edge and memory
- Why the messages field needs an append reducer
- Part 2: cosine-similarity retrieval in pure NumPy
- The follow-up questions interviewers ask after your code runs
- Common coding-round mistakes, and how to talk while you code

## Chapters

- [0:00](https://youtu.be/YsTsbze0Glo?t=0) Intro
- [0:35](https://youtu.be/YsTsbze0Glo?t=35) Task 1: a LangGraph agent
- [1:49](https://youtu.be/YsTsbze0Glo?t=109) The agent: state and reducer
- [2:42](https://youtu.be/YsTsbze0Glo?t=162) Nodes and the conditional edge
- [4:37](https://youtu.be/YsTsbze0Glo?t=277) Task 2: retrieval in pure NumPy
- [5:08](https://youtu.be/YsTsbze0Glo?t=308) Retrieval: embed, normalise, search
- [6:50](https://youtu.be/YsTsbze0Glo?t=410) Mistakes, and how to talk while coding

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In the last part we designed a company document assistant in thirty five minutes. Now, the coding round. Two tasks, twenty minutes each, from a completely blank file.

The coding round checks three things. Can you write working code without a template? Can you explain the pieces? And do you test as you go? Remember: a plain answer that runs scores higher than a beautiful one that does not.

**Three things the interviewer watches**

- Can you produce working code without a template?
- Can you explain each piece as you write it?
- Do you test as you go?

*Plain code that runs beats beautiful code that doesn't.*

## Task 1: a LangGraph agent

Task one. Pause and read it, then try it yourself before watching my walkthrough.

Build a LangGraph agent that answers, what is the top fund on the nineteenth of June twenty twenty five, by calling our fund ranking tool. One tool. A fake LLM that routes by keyword, so no API key is needed. A conditional edge. And memory with a thread id. It must run.

**Answer “What is the top fund on 2025-06-19?”**

- One tool: rank_funds from core/fund_model.py
- A fake LLM: a keyword router instead of a real model
- A conditional edge: tool call pending → tools, else END
- Memory: a MemorySaver checkpointer with a thread id
- It must run and print the answer

Before typing a single line, restate the task out loud, and say your plan. This takes thirty seconds and stops you solving the wrong problem for five minutes.

**Restate the task out loud first**

> **“One tool, a keyword router, a conditional edge, memory. State first, then the fake model, then nodes, then the graph. I'll run after each step.”**

Here is the build order, with a clock. Two minutes for imports, and call the tool once by itself, so you know it works. Then the state, the fake model, the nodes, and finally the graph. Notice the third column: you run something after almost every block, so errors arrive one at a time, not ten at once.

**Twenty minutes, block by block**

| Minutes | Write | Then |
|---|---|---|
| 0 – 2 | Imports, the ranking tool | Call the tool once |
| 2 – 5 | State with an append reducer | — |
| 5 – 10 | The fake LLM | Test it on one message |
| 10 – 14 | The two nodes | — |
| 14 – 20 | Graph, memory, invoke | Run, read the output aloud |

Step one, the state. Think of the state as a shared whiteboard every step reads and writes. The key line is the reducer: the append function tells LangGraph to add new messages to the history instead of replacing it. Pending holds the tool calls for the current step only, so it is simply overwritten.

**Messages are appended, never overwritten**

`day10_mock/coding_round_agent.py`
```python
import json, re
from typing import Annotated, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from core.fund_model import rank_funds

def append(a: list, b: list) -> list:
    return a + b

class State(TypedDict):
    messages: Annotated[list[dict], append]
    pending: list[dict]
```

Step two, the fake model. It has the same complete method a real model adapter would have. On the first pass it looks for words like top or rank, pulls out the date, and asks for the tool. On the second pass it reads the tool result and writes the answer. Notice the numbers are formatted from the tool's result, never typed by hand.

**Route by keyword, narrate the tool result**

`day10_mock/coding_round_agent.py`
```python
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
```

Step three, two nodes. A node is just a function with one job. The LLM node calls the model and records any tool calls. The tool node runs them. The important part is the try and except: if the tool fails, the error goes back to the model as data. One bad date should never crash the whole request.

**Tool errors go back as data, never a crash**

`day10_mock/coding_round_agent.py`
```python
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
```

Step four, the graph. The route function reads the state: if a tool call is pending, go to tools, otherwise finish. Map both outcomes, tools and END, or the graph will never stop. Tools always go back to the LLM. Then compile with a memory checkpointer, and invoke with a thread id, which is like a conversation's ticket number.

**One conditional edge is the whole agent loop**

`day10_mock/coding_round_agent.py`
```python
def route(state: State) -> str:
    return "tools" if state["pending"] else END

g = StateGraph(State)
g.add_node("llm", llm_node)
g.add_node("tools", tool_node)
g.add_edge(START, "llm")
g.add_conditional_edges("llm", route, {"tools": "tools", END: END})
g.add_edge("tools", "llm")
app = g.compile(checkpointer=MemorySaver())

cfg = {"configurable": {"thread_id": "mock-1"}}
out = app.invoke({"messages": [{"role": "user", "content": q}],
                  "pending": []}, config=cfg)
```

Run it with python day ten mock, coding round agent dot py. Your exact numbers depend on the synthetic data, but the shape looks like this. The top fund came from the tool. And the fourteenth of June twenty twenty five was a Saturday, so the tool returns an error, and the agent says so plainly instead of guessing.

**python day10_mock/coding_round_agent.py**

> **User:** What is the top fund on 2025-06-19?
>
> **Assistant:** Top fund on 2025-06-19: Bharat Growth Fund, predicted +0.53%
>
> **User:** Rank funds on 2025-06-14
>
> **Assistant:** I could not answer: no data for 2025-06-14 (not a trading day). Try a nearby weekday.

Once it runs, expect follow ups. Why two passes? The first decides, the second answers. How does memory survive a restart? Swap the in memory checkpointer for a database one; the graph does not change. A real model? Same method, behind an adapter. And what stops an infinite loop? A counter in the state, ending after, say, five tool rounds.

**What they ask once it runs**

| Question | Your answer |
|---|---|
| Why two passes through the LLM node? | Pass 1 decides on a tool; pass 2 reads the result |
| How does memory survive a restart? | Swap MemorySaver for a database checkpointer |
| How do you plug in a real model? | Same complete() method, behind an adapter |
| What stops an infinite loop? | A tool-round counter in state; END after 5 |

## Task 2: retrieval in pure NumPy

Task two. Retrieval, the heart of RAG, with nothing but NumPy.

Given five short documents, embed them with any simple scheme, normalise the vectors, score a query by cosine similarity, and return the best match. No scikit learn and no embedding model. Cosine similarity measures whether two arrows point the same way, ignoring how long they are.

**Find the best document for a question**

1. Embed five short documents with a simple scheme
2. Normalise each vector to length 1
3. Score a query by cosine similarity; return the top result

*Pure NumPy and the standard library. No embedding model.*

Step one. Build a vocabulary of every word in the documents. Then a document's vector is just a count of how often each word appears. It is crude, but deterministic, and enough to show the mechanics. Words in a query that are not in the vocabulary are simply ignored.

**A bag-of-words vector: count the words**

`day10_mock/coding_round_retrieval.py`
```python
DOCS = [
    "NAV is the net asset value of one unit of a mutual fund.",
    "The expense ratio is the yearly fee a fund charges, as a share of assets.",
    "A SIP is a systematic investment plan that invests a fixed amount every month.",
    "Walk-forward validation trains on the past and tests on the next window.",
    "MCP is a protocol that lets an agent discover and call tools on a server.",
]
def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())
VOCAB = {w: i for i, w in enumerate(sorted({w for d in DOCS for w in tokenize(d)}))}
def embed(text):
    v = np.zeros(len(VOCAB))
    for w in tokenize(text):
        if w in VOCAB:
            v[VOCAB[w]] += 1.0
    return v
```

Step two. Divide each vector by its length, so every vector has length one. Now cosine similarity is just a dot product, and scoring every document is one matrix multiplication. The documents are normalised once, up front. And the guard stops a divide by zero when a query has no known words.

**Unit vectors make cosine a dot product**

`day10_mock/coding_round_retrieval.py`
```python
def normalise(m):
    norms = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(norms == 0, 1.0, norms)   # no divide-by-zero

D = normalise(np.stack([embed(d) for d in DOCS]))  # (5, |V|)

def search(query, k=1):
    q = normalise(embed(query))
    scores = D @ q                     # cosine = dot of unit vectors
    order = np.argsort(-scores)[:k]
    return [(int(i), round(float(scores[i]), 3)) for i in order]
```

Run it. The first three queries find the right document. But look at the last one: the price of gold matches the NAV document, with a high score, only because of common words like what, is and the. There is no right answer, yet it returns one anyway.

**python day10_mock/coding_round_retrieval.py**

| Query | Top doc | Score |
|---|---|---|
| What is the expense ratio of a fund? | expense ratio | 0.78 |
| how does a SIP invest every month | SIP | 0.67 |
| how does an agent call tools? | MCP | 0.49 |
| what is the price of gold | NAV  (wrong!) | 0.60 |

*Point out the weaknesses yourself, before you are asked.*

Saying this before you are asked is a strong signal. Invest and invests do not match here; a real embedding model fixes that. Common words inflate scores, so remove them or weight words by rarity. Add a minimum score, the same no answer threshold from the design round. And at ten million chunks, use an approximate nearest neighbour index.

**Name the limits, then the fixes**

- “invest” vs “invests” don't match: stemming or a real embedding fixes it
- Common words inflate scores: stop-words or TF-IDF weighting
- No relevant document? Add a minimum score, then say “no answer”
- Ten million chunks? An approximate nearest-neighbour index
- Make it hybrid: add a keyword score, fuse the rankings

## Mistakes, and how to talk while coding

Finally, the mistakes that sink most candidates in this round, and how to keep talking without rambling.

Writing everything and running once at the end, which gives you ten errors at once. Forgetting the reducer, so the second pass cannot see the tool result. A conditional edge without END. Attaching a checkpointer but invoking without a thread id. And normalising columns instead of rows. Each one is avoided by running after every block.

**What costs candidates the round**

| Mistake | Do instead |
|---|---|
| Writing everything, running once at the end | Run after each block |
| No reducer on messages | Annotated[list[dict], append] |
| Conditional edge without END | Map both tools and END |
| Checkpointer, but no thread id | Pass a configurable thread_id |
| Normalising the wrong axis | axis=-1, then check one row's norm |

And talk while you code. Restate the task first. At each block, say what it is for, not the syntax. When you hit an error, read it out loud, form a guess, and test it. Calm debugging is a strong positive signal. If you forget an API, say so. And at the end, run it and name one limitation before you are asked.

**Narrate the why, not the syntax**

1. Before typing: restate the task and your plan
2. Each block: say what it is for
3. On an error: read it aloud, guess why, test it
4. Forgot an API? Say so, then check the signature
5. At the end: run it, read the output, name one limit

Quick check. In the agent, what breaks if the messages field has no append reducer? Pause and answer. Each node would overwrite the history, so on the second pass the model could not see the tool result, and the agent loses the conversation.

**Quick check:** In the agent, what breaks if the messages field has no append reducer?

<details><summary>Answer</summary>

Each node's messages replace the history, so the second LLM pass can't see the question or the tool result.

</details>

Let's recap. Restate, then build and run block by block. The agent is a state with a reducer, a model, two nodes, and one conditional edge. Errors come back as data. Retrieval is count, normalise, multiply. And always name the limits yourself. In the final part: the behavioural round, and a send off for the series.

- Restate the task, then build and run block by block
- Agent: state + reducer, fake LLM, two nodes, one conditional edge
- Tool errors return as data; numbers come from the tool
- Retrieval: count words, normalise, one matrix product
- Name the limits and fixes before you are asked

Both files are in the day ten folder of the repository. Write each one from a blank file three times, timed. See you in the final part.

---

← [Day 10, Part 2](day10_p2.md) · [All lessons](README.md) · [Day 10, Part 4](day10_p4.md) →
