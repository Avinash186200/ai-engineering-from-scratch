# Day 18, Part 2: Testing AI Agents: Long Threads, Journeys, Thresholds

**Watch:** video coming soon · **Code:** [`day18_agent_testing/`](../day18_agent_testing/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

"Have you tested the long threads by hand?" This episode turns that answer into a yes. You will find where the threads are defined, read one out loud, replay it turn by turn, and then learn how a journey is scored, and why four steps out of five is still a fail.

## What you will learn

- What a long thread is, and why agents break as conversations grow
- How to find where tests are defined, starting from the runner
- Replaying a thread by hand, and editing a turn to test an idea
- Threads vs journeys: mechanics per turn vs one user goal
- Pass thresholds, repeated runs and hard checks for dates and numbers

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In part one we saw why a pass rate is not understanding, and why a multi turn test catches a bug that the same question, asked alone, does not. Today: long threads and journeys.

In the review, the key question was: have you tested the long threads by hand? Turn by turn? The answer was no. By the end of this video, yours will be yes, and you will be able to show it.

**Have you tested them by hand?**

> **Turn by turn. Every one.**
> In the review, the answer was no. Today it becomes yes.

## What a long thread is

First, what a long thread is, and why it exists.

A long thread is a multi turn test. Think of it like a play script. Each turn has a line for the user, and the call we expect the agent to make. In the lab the threads have four or five turns, so they are easy to read. In production they often have ten or more. You write them once, and replay them on every change.

**A scripted conversation, many turns**

- A multi-turn test: each turn is a user message plus the expected call
- In the lab: four or five turns; in production: ten or more
- Written once, replayed on every change

Why bother? Because agents break as conversations grow. The context window fills up. Older turns get summarised or cut to save space. The model drifts. A date set in turn two is a long way back by turn nine. Short tests never see any of this.

**Things break with length**

- The context window fills up
- Old turns get summarised or cut
- The model drifts away from early facts
- A date from turn 2 is far away by turn 9

## Find it, read it

Step one is boring, and it is the step that failed in the review: find the test.

Do not guess. Open the runner and find the line that loads the tests. In run threads dot py, two lines name the folders: tests slash threads and tests slash journeys. Load cases reads every YAML file in each, in sorted order. Now you can say exactly where the tests come from. Not somewhere in end to end. This folder, this loader.

**Start from the runner**

`python`
```python
THREADS_DIR = HERE / "tests" / "threads"
JOURNEYS_DIR = HERE / "tests" / "journeys"

def load_cases(threads_dir=THREADS_DIR, journeys_dir=JOURNEYS_DIR):
    for kind, d in (("thread", threads_dir), ("journey", journeys_dir)):
        for p in sorted(Path(d).glob("*.yaml")):
            ...
```

Then list both folders. Three threads: bond followup, explicit dates and outlook as of. One journey: morning check. Say the number out loud. Three threads and one journey. If someone asks how many, you answer in one second.

**Count them, out loud**

`output`
```text
tests/threads:
  bond_followup.yaml
  explicit_dates.yaml
  outlook_as_of.yaml
tests/journeys:
  morning_check.yaml
```

Now read one out loud. Outlook as of. Turn one, good morning, expect no tool. Turn two, what date is the data: expect get snapshot date, and the answer must contain the snapshot date and the latest available date from the tool. Turn three, give me the five day outlook as of that date: expect get outlook, horizon five, as of the thirteenth. Turn four, and the twenty one day, and so on.

**Read it like a script**

`yaml`
```yaml
thread: outlook_as_of
turns:
  - user: "Good morning"
    expect_tool: null
  - user: "What date is the data? Is it fresh?"
    expect_tool: get_snapshot_date
    grounded_keys: [snapshot_date, latest_available]
  - user: "Give me the 5-day outlook as of that date"
    expect_tool: get_outlook
    expect_params: {horizon_days: 5}
    expect_as_of: "2026-11-13"
  - user: "and the 21-day?"
    ...
```

That is the level the lead wanted. Not: it tests end to end behaviour. But: turn three expects get outlook, five days, as of the thirteenth of November. Specific enough that anyone can check it on screen.

**Not "it tests end-to-end"**

> **"Turn 3 expects get_outlook, 5 days, as of 2026-11-13"**
> Specific enough that anyone can check it on screen.

## Replay it by hand

Now the key skill. Replay.

Run one thread with the replay flag. Before each turn it shows the user message and waits. Enter runs it, e lets you edit the text, q quits. Turn one, no tool, good. Turn two calls get snapshot date, and the answer says: the latest complete snapshot is the thirteenth, and a partial load exists for the fourteenth. Write the thirteenth down. That date must survive every later turn.

**One turn, then pause**

`output`
*(output trimmed)*

```text
[outlook_as_of:t1] user> Good morning
  Enter = run, e = edit text, q = quit:
  PASS  ... tool=None params=None as_of=None
        answer: Good morning! I can tell you the data date, ...
[outlook_as_of:t2] user> What date is the data? Is it fresh?
  PASS  ... tool=get_snapshot_date params={} as_of=None
        answer: The latest complete snapshot is 2026-11-13
        (5 days old, so not fresh). A partial load exists for 2026-11-14.
```

At turn three, press e, and type the date yourself: give me the five day outlook as of the thirteenth. It passes. Rates minus two point four basis points. That one edit tells you a lot. The tool works. The data for the thirteenth is there. So the problem is not the tool. It is how that date gets resolved. You learned that in ten seconds, without touching any code.

**Test an idea without changing code**

`output`
*(output trimmed)*

```text
[outlook_as_of:t3] user> Give me the 5-day outlook as of that date
  Enter = run, e = edit text, q = quit: e
  new text> Give me the 5-day outlook as of 2026-11-13
  PASS  ... tool=get_outlook params={'horizon_days': 5, 'as_of': '2026-11-13'}
        answer: 5-day outlook as of 2026-11-13: rates -2.4 bp,
        spreads 0.8 bp (confidence 0.64).
```

As the lead said in that review: you run them one by one. That is all it is. Turn by turn. It is not clever. It is careful.

**You run them one by one**

> **That is all it is.**
> It is not clever. It is careful.

While you replay, watch for four things. A wrong or missing tool. The right tool with a wrong parameter, and check dates first. A number in the answer that the tool never returned. That one is easy to miss. And the agent asking again for something it already had.

**Four things to watch**

- Wrong tool, or a missing tool call
- Right tool, wrong parameter: check dates first
- A number in the answer that the tool did not return
- The agent asks again for something it already had

Let's replay a second thread together, bond followup. Turn one is explicit: pool A thirty, the twelfth. Turn two: and its duration as of then. Its must mean pool A thirty, and then must mean the twelfth. Turn three switches to pool B fifteen, and the date silently stays the twelfth. Turn four: and that one as of the thirteenth. That one is pool B fifteen, with a new date. Four turns, four different ways to resolve a reference. All four pass, and now you can say why.

**Every pronoun must resolve**

| Turn | User says | Must resolve to |
|---|---|---|
| t1 | OAS of POOL-A30 as of 2026-11-12? | POOL-A30, 2026-11-12 (explicit) |
| t2 | And its duration as of then? | its = POOL-A30, then = 2026-11-12 |
| t3 | Convexity of POOL-B15? | new pool, date still 2026-11-12 |
| t4 | And that one as of 2026-11-13? | that one = POOL-B15, new date |

You don't replay everything every day. But replay every thread once when you take ownership. Replay any failing thread before you say anything about it. And replay after any change to the prompt, the tools, or how memory works.

**When to replay**

- Every thread, once, when you take ownership
- Every failing thread, before you say a word about it
- After any change to the prompt, the tools or memory

## Journeys

Now journeys. The second question in the review: where are they, how many, and what do they measure?

A thread checks the mechanics: right tool, right parameters, right date, on every turn. A journey checks a goal. A person arrives wanting something. Do they get it? A journey has steps, and a pass threshold: how many steps must pass for the goal to count as done.

**Thread vs journey**

- **Thread**
  - Checks the mechanics
  - Every turn must pass
  - Tools, parameters, dates
- **Journey**
  - Checks one user goal
  - Steps must reach a threshold
  - Written as the user's day

Here is the one journey, morning check. It is the start of an analyst's day. Say good morning, check how fresh the data is, read the five day and twenty one day outlooks, and check one bond, all as of the snapshot. Each step has the same kind of checks as a thread. The key line is the pass threshold: required five, of five.

**A journey: start of day**

`yaml`
```yaml
journey: morning_check
description: Start of day, check freshness, read both outlooks
             and one bond as of the snapshot
pass_threshold: {required: 5, of: 5}
turns:
  - user: "Good morning"
  - user: "What date is the data? Is it fresh?"
  - user: "Give me the 5-day outlook as of that date"
  - user: "and the 21-day?"
  - user: "What is the OAS of POOL-B15 as of then?"
```

Run it alone with dash dash thread morning check. Steps one and two pass. Step three fails with the same message as before: as of, expected the thirteenth, got the fourteenth. Steps four and five pass. Four of five steps passed, required five, so the journey fails. Eighty percent sounds good. But the person using this saw a five day outlook from the wrong data. For them, the morning check is broken.

**Four out of five is a fail**

`output`
```text
[journey] morning_check  (morning_check.yaml)
  PASS  turn_id=morning_check:t1 tool=None
  PASS  turn_id=morning_check:t2 tool=get_snapshot_date
  FAIL  turn_id=morning_check:t3 tool=get_outlook
        - as_of: expected 2026-11-13 got 2026-11-14
  PASS  turn_id=morning_check:t4 tool=get_outlook
  PASS  turn_id=morning_check:t5 tool=get_bond_metrics
  journey morning_check: 4/5 steps passed, required 5 -> FAIL
```

Look at it step by step. One means pass, zero means fail. Only step three is red. And notice: it is the same user words as outlook as of, turn three, with the same wrong date. Two red cases in the report, but one bug. When you report, say that clearly. Do not count it as two problems.

**One bad step breaks the goal**

- t1 greeting: 1
- t2 data date: 1
- t3 5-day: 0
- t4 21-day: 1
- t5 POOL-B15: 1

*Same root cause as outlook_as_of:t3. Two red cases, one bug.*

So now you can answer the lead's four questions in under a minute. Where: the journeys folder. How many: one, morning check. What it measures: the start of day check, with every number as of the snapshot. And you can walk it end to end, using replay.

**Four questions about journeys**

- Where? day18_agent_testing/tests/journeys/
- How many? One: morning_check
- What does it measure? A start-of-day check, all as of the snapshot
- Walk it end to end with --thread morning_check --replay

## Thresholds

Finally, thresholds. They look harmless. They are not.

A threshold is a decision about which failures you accept. If morning check said required four of five, it would pass today. And the step it let through is the one that gave a number from the wrong date. That is not a small failure. That is the failure.

**A threshold is a decision**

> **It decides which failures you accept**
> 4 of 5 means one step may be wrong. If that step gives a number from the wrong date, a user saw a wrong number.

One more idea. The lab's agent is scripted, so every run gives the same result, and exact checks make sense. With a real model, wording and even tool calls can vary from run to run. Then you run each thread several times and track a pass rate, like nine of ten runs. The lab has an optional real model mode, and its own guide says: treat the threads as evals with a pass rate, not exact tests.

**Steps per run vs runs per test**

- **Scripted (lab default)**
  - Same result every run
  - Exact checks, N of N
  - One run is enough
- **Real model**
  - Wording and calls can vary
  - Run each thread several times
  - Track a pass rate per thread

So, four rules. Some checks are hard gates: a wrong date or a wrong number fails, whatever the score. Any run below one hundred percent: open its trace anyway. Pick a pass rate from many runs of a version you trust, just under its normal range. And write down why, next to the number, so the next person does not lower it to get a green build.

**Thresholds without surprises**

1. Hard checks: a wrong date or a wrong number fails, whatever the score
2. Any run below 100%: open its trace anyway
3. Set a pass rate from many runs of a version you trust
4. Write the reason next to the number

Quick check. Pause and answer. Morning check passes four of five. Someone proposes changing the threshold to four, so the build goes green. What do you say? No. The failing step gives a number from the wrong date. Lowering the bar hides the bug. Fix the bug, and keep five of five.

One more. In replay, typing the date yourself at turn three passes. What does that rule out? The tool, and the data for the thirteenth. Both work. So the fault is in how that date gets resolved. That is the first clue for part four.

**Quick check:** Replay: typing the date explicitly at t3 passes. What does that rule out?

<details><summary>Answer</summary>

The tool and the data for 2026-11-13. The fault is in resolving "that date".

</details>

Let's recap. Long threads catch bugs that only appear as conversations grow. Find tests from the runner, name the folder, and count them. Replay turn by turn, and use edit to test an idea without touching code. Threads check mechanics, journeys check one goal. And four out of five is a fail when the bad step gives a wrong number. Next: writing tests as YAML, and tracing.

- Long threads catch bugs that appear only as chats grow
- Find tests from the runner; name the folder and count them
- Replay turn by turn; use e to test an idea
- Threads check mechanics; journeys check one goal
- 4 of 5 is a fail when the bad step is a wrong number

The threads, the journey and the replay runner are linked in the description. Replay all three threads yourself before the next part. If this helped, subscribe, and I will see you in the next video.

---

← [Day 18, Part 1](day18_p1.md) · [All lessons](README.md) · [Day 18, Part 3](day18_p3.md) →
