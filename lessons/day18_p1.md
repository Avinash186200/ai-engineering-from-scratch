# Day 18, Part 1: Testing AI Agents: Pass Rate Is Not Understanding

**Watch:** video coming soon · **Code:** [`day18_agent_testing/`](../day18_agent_testing/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Twenty-six of twenty-eight tests passed. Which two failed? Walk me through one. (That 26-of-28 suite is the story's, not the lab's. The lab has four threads (three threads and one journey) and seventeen pytest tests.) This episode starts a new block on testing and debugging chatbots and agents. We begin with a review story (roles only, no names), the standard it set, the lab we use for the whole day, and the difference between single-turn and multi-turn tests.

## What you will learn

- Why a pass rate is a starting point, not an answer
- The four-part standard: read it, replay it, show the tool calls, trace every failure
- The course lab: a small fixed-income agent, three tools and one planted bug
- Single-turn tests vs multi-turn tests, and the state that must carry over
- How the same question passes alone and fails inside a conversation

## Lesson notes

Slide content and the full narration, in order.

Hi, I'm Avinash, and welcome to day eighteen of AI Engineering from Scratch. This starts a new block, and it is about one skill: testing and debugging chatbots and agents properly. Not just running the tests. Understanding them, well enough to show anyone, on screen, what each test does and why it failed. As always, no machine learning background is needed.

Picture this. You report: twenty six of twenty eight tests passed. Sounds good. Then someone asks: which two failed? Walk me through one. And the room goes quiet. This whole day is about never being in that room. One note: that twenty six of twenty eight suite is the story's, not the lab's. The lab has four threads, three threads and one journey, and seventeen pytest tests.

**26 passed, 2 failed**

> **Which two failed? Walk me through one.**
> If you cannot answer on screen, you do not own the tests yet.

Here is the plan. Part one: the standard, the lab and single versus multi turn tests. Part two: long threads and journeys. Part three: writing tests as YAML, and tracing. Part four: we debug a planted bug live, then use test driven development. And part five: browser smoke tests, triage and release discipline.

**The plan for Day 18**

- Part 1: the standard, the lab, single vs multi-turn
- Part 2: long threads and journeys
- Part 3: tests as YAML, and tracing
- Part 4: debugging the planted bug, and TDD
- Part 5: browser smoke tests, triage and release

## The review story

Let me start with a story. It is a typical review scenario (illustrative), and I use roles only, no names.

A team runs a chat agent in production. It answers questions about bonds and mortgage backed securities. It never makes up numbers. It calls tools, and every tool result is tied to a date, the as of date of the data snapshot. Two junior engineers were asked to own the tests.

**An agent in production**

- A chat agent answers fixed-income and MBS questions
- It does not invent numbers: it calls tools
- Every tool result is as of a snapshot date
- Two junior engineers own the tests

They came with pass counts and a short summary. The engineering lead asked: pick one long thread, what does it check? The answer was general. So the lead asked: open the file. Which two failed? Walk me through one. Words only go so far.

**One question changed everything**

> **User:** Pick one long thread. What does it check?
>
> **Assistant:** They test end-to-end behaviour, multi-turn...
>
> **User:** Open the file. Which two failed? Walk me through one.

Engineer A knew the threads existed, but could not find the file that defined them. Engineer B said all twenty eight journeys passed, but the lead's own run showed two failures, and nobody had traced them. And when the lead asked, have you replayed these long threads by hand, turn by turn, the honest answer was no.

**Where it fell apart**

- Engineer A could not find the file that defines the threads
- Engineer B reported 28 of 28; the lead's own run had 2 failures
- Nobody had replayed a long thread by hand
- They had numbers, not understanding

Nobody was lazy. They ran the tests and reported the numbers, and that feels like work. But look at the gap. The lead wanted the file, each turn, each tool call with its parameters, and the reason for every failure. The point was never running the tools. The point was understanding them.

**What they brought vs what was asked**

- **Brought**
  - Pass and fail counts
  - A high-level summary
  - We ran the suite
- **Asked**
  - Where is the test defined?
  - What does each turn do?
  - Which tool, which parameters?
  - Why did it fail?

## The standard

So what does good look like? Here is the standard I now use, and the one we practise all day.

Four things. One, open any test and read it out loud. Two, replay it by hand, one turn at a time. Three, show which tool was called on each turn, and with which parameters. Four, every failing test is reproduced and traced to a cause. Not most failures. Every failure.

**Four things you must be able to do**

1. Read any test out loud, turn by turn
2. Replay any test by hand
3. Show every tool call and its parameters
4. Reproduce and trace every failing test

Why is this harder for agents? In normal code, a failing test points at a line. In an agent, it points at a conversation. The bug could be in the prompt, the tool, the memory of earlier turns, the step that decides which tool to call, or even the test itself. You cannot guess. You have to look.

**A failure points at a conversation**

> **Prompt? Tool? Memory? The test itself?**
> You cannot guess. You have to look.

## The course lab

To practise, we have a small lab in the repo. Everything today runs on it, offline, with no API key.

Here is the lab folder, day eighteen agent testing. The agent lives in fi agent slash agent dot py. The tools are in tools dot py, and tracing dot py writes a trace file for every run. The runner is run threads dot py. Show trace prints the trace of one turn. There is a small chat page, three YAML threads, one journey called morning check, and a browser smoke test. That is the whole lab. Nothing hidden.

**day18_agent_testing/**

`files`
```text
fi_agent/agent.py       the agent, its state, one planted bug
fi_agent/tools.py       three fake, deterministic tools
fi_agent/tracing.py     writes traces/<run_id>.jsonl
run_threads.py          runs every thread and journey
tools/show_trace.py     prints the trace tree of a turn
web/app.py              a small chat page
tests/threads/          bond_followup, explicit_dates, outlook_as_of
tests/journeys/         morning_check
tests/ui/test_smoke.py  a browser smoke test
```

Three tools. Get snapshot date tells you the date of the last complete snapshot. Get outlook takes a horizon of five or twenty one days and an as of date, and returns the expected change in rates and spreads, in basis points. Get bond metrics takes a pool ID, like pool A thirty, and an as of date, and returns its option adjusted spread, duration and convexity. Two of the three tools need a date. Keep that in mind.

**Three tools, two need a date**

`tools`
```text
get_snapshot_date()
    -> snapshot_date 2026-11-13, latest_available 2026-11-14

get_outlook(horizon_days, as_of)
    -> rate and spread change in bp, for 5 or 21 days

get_bond_metrics(bond_id, as_of)
    -> OAS, effective duration, convexity (POOL-A30, POOL-B15)
```

The data has two dates. Thirteenth November twenty twenty six is the last complete snapshot. It is five days old, so not fresh, but it is complete. Fourteenth November is a newer partial load, still filling in. Answering from the partial load by mistake is the classic bug: the answer looks fine, and it is from the wrong data.

**A complete snapshot and a partial load**

| Date | What it is | Safe to answer from? |
|---|---|---|
| 2026-11-13 | Last complete daily snapshot, 5 days old | Yes |
| 2026-11-14 | Newer partial load, still filling in | No |

Run python day eighteen agent testing slash run threads dot py. The first line gives a run ID and the trace file. Two threads pass. Outlook as of fails at turn three: as of, expected the thirteenth, got the fourteenth. The journey morning check passes four steps of five, and needs five, so it fails. Two of four passed. The old me would report: two failures. The new me says: turn three of outlook as of, here is the file, here is the call, let me show you. We find the cause in part four.

**Run the suite (shortened)**

`output`
*(output trimmed)*

```text
run_id=run-20261118-231305-c6b6  trace=.../traces/run-20261118-231305-c6b6.jsonl
[thread] bond_followup   4 of 4 PASS
[thread] explicit_dates  4 of 4 PASS
[thread] outlook_as_of
  FAIL  turn_id=outlook_as_of:t3 tool=get_outlook
        - as_of: expected 2026-11-13 got 2026-11-14
[journey] morning_check
  journey morning_check: 4/5 steps passed, required 5 -> FAIL
2/4 passed; FAILED: outlook_as_of, morning_check
```

## Single-turn vs multi-turn

Now the first big idea. Two kinds of test.

A single turn test is simple. One message in, then check the result. Not just the answer text: check the tool call. Did the agent pick get bond metrics? Did it pass the right pool and the right date? And is the number in the answer the one the tool returned? Tests like this are cheap and fast, and they catch a lot.

**One message in, check the tool call**

`yaml`
```yaml
turns:
  - user: "What is the OAS of POOL-A30 as of 2026-11-12?"
    expect_tool: get_bond_metrics
    expect_params: {bond_id: POOL-A30}
    expect_as_of: "2026-11-12"
    grounded_keys: [oas_bp]
```

But they have one big blind spot. No history. Every single turn test starts with an empty conversation. Real users never talk like that.

**Single-turn tests have no history**

> **Every test starts fresh**
> Real users never do.

Here is how people really talk, taken from the outlook as of thread. Good morning. What date is the data? Is it fresh? The agent says: the latest complete snapshot is the thirteenth, five days old, and a partial load exists for the fourteenth. Then: give me the five day outlook as of that date. That date only means something because of turn two.

**"That date" needs turn 2**

> **User:** Good morning
>
> **User:** What date is the data? Is it fresh?
>
> **Assistant:** The latest complete snapshot is 2026-11-13 (5 days old, so not fresh). A partial load exists for 2026-11-14.
>
> **User:** Give me the 5-day outlook as of that date

Now a worked example. Send exactly the same words to a fresh agent, as a single turn test. The call is get outlook, five days, as of the thirteenth. Correct. It passes. Now send the same words inside the conversation, after turn two. The call uses the fourteenth. Wrong. Same words, same code, different result. The only difference is history. A single turn suite would be all green, and the bug would ship.

**Same words, fresh conversation**

`python, from day18_agent_testing/`
```python
from fi_agent.agent import Agent

Agent().turn("Give me the 5-day outlook as of that date").first_call["params"]
# {'horizon_days': 5, 'as_of': '2026-11-13'}    correct

# Inside outlook_as_of, after turn 2:
# {'horizon_days': 5, 'as_of': '2026-11-14'}    wrong
```

So what carries over? In the lab, it is the conversation state in agent dot py. As of, the date the user anchored to. Latest available, the newest partial load, learned from get snapshot date. Last horizon, so that, and the twenty one day, works. And last bond, so that its and that one work. Each of these is a place for a bug, and a multi turn test checks them on every turn, not only at the end.

**State that lives between turns**

- as_of: the date the user anchored to
- latest_available: the newest partial load
- last_horizon: so 'and the 21-day?' works
- last_bond: so 'its' and 'that one' work

Here is the whole thread, read the way the lead wanted. Turn one, a greeting, no tool. Turn two, the date question, get snapshot date. Turn three, the five day outlook as of that date, which should be the thirteenth. It fails. Turn four, and the twenty one day, still the thirteenth, passes. Turn five, the duration of pool A thirty as of then, passes. One bad turn out of five. That is exactly the kind of failure a pass rate hides.

**outlook_as_of, turn by turn**

| Turn | User says | Expected call | Result |
|---|---|---|---|
| t1 | Good morning | no tool | PASS |
| t2 | What date is the data? | get_snapshot_date | PASS |
| t3 | 5-day outlook as of that date | get_outlook 5, 2026-11-13 | FAIL |
| t4 | and the 21-day? | get_outlook 21, 2026-11-13 | PASS |
| t5 | duration of POOL-A30 as of then | get_bond_metrics, 2026-11-13 | PASS |

And look at what the wrong date does to the answer. On the thirteenth, the five day outlook says rates fall two point four basis points. On the partial load, it says rates rise one point seven. The direction flips. The tool does not error. The sentence reads perfectly. It is just from the wrong data. In finance, that is a real mistake, and only a check on the as of argument catches it.

**No error. Plausible numbers. Wrong date.**

> **Rates -2.4 bp became rates +1.7 bp**
> The answer reads perfectly. The direction is flipped, and nothing errors.

So write both. Single turn tests for tool choice and parameter shape. Lots of them. Multi turn tests for anything with memory, checking the call on every turn, not just the last answer. A simple rule: if a user could say that, then, its or again, you need a multi turn test.

**How to mix them**

- **Single-turn**
  - Tool choice
  - Parameter shape
  - Many of them
- **Multi-turn**
  - Anything with memory
  - Check state on every turn
  - Fewer, but deeper

*If a user could say "that", "then", "its" or "again", write a multi-turn test.*

Quick check. Pause and answer. Every single turn test passes. Can a follow up question still use the wrong date? Yes. Single turn tests never check what carries over. Only a multi turn test, checking as of on every turn, catches it.

One more. Turn three used the wrong date. So why does turn four pass? Pause and think. The answer: the wrong date was used for that one call, but the date stored in the conversation state was still the thirteenth. So the next turn picks up the right date again. We will see this in the trace in part four. It is also why a bug like this is easy to miss: one bad turn, then everything looks normal.

**Quick check:** In outlook_as_of, turn 3 used the wrong date. Why might turn 4 still pass?

<details><summary>Answer</summary>

The wrong date was used for one call, but the stored as_of stayed 2026-11-13. Part 4 shows this in the trace.

</details>

Let's recap. A pass rate is a starting point, not an answer. Read every test, replay it, show the tool calls, and trace every failure. The lab has three tools, a complete snapshot on the thirteenth and a partial load on the fourteenth. Single turn tests check tools, multi turn tests check memory. And wrong dates hide behind plausible numbers. Next: long threads and journeys.

- A pass rate is a starting point, not an answer
- Read it, replay it, show the tool calls, trace every failure
- The lab: three tools, a complete snapshot and a partial load
- Single-turn tests check tools; multi-turn tests check memory
- Wrong dates hide behind plausible numbers

The lab, the YAML threads and the trace viewer are linked in the description. Run the threads yourself before the next part. If this helped, subscribe, and I will see you in the next video.

---

[All lessons](README.md) · [Day 18, Part 2](day18_p2.md) →
