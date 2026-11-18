# Day 18, Part 4: Debugging an AI Agent: Failing Test to Fix, Then TDD

**Watch:** video coming soon · **Code:** [`day18_agent_testing/`](../day18_agent_testing/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

One test is red: outlook_as_of, turn 3. This episode follows it all the way: reproduce, read the YAML, replay, open the trace, find the divergent call, read the code, make a one-line fix and prove it. Then we use the same loop to build tests first.

## What you will learn

- A seven-step method for any failing agent test
- How to compare a failing turn with a passing one in the trace
- Finding the divergent call, and why the prompt was not the problem
- Fixing, re-running, and reading the tests that turn red on purpose
- Test-driven development for agents, and why every bug becomes a test

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In part three we wrote tests as YAML and learned to read a trace. Today we use both on the real failure, from start to finish. No guessing.

Here is the red line. Outlook as of, turn three. The tool is right, get outlook. The horizon is right, five. Only the date is wrong: expected the thirteenth, got the fourteenth. The runner prints the expected call and the actual call one under the other, so the difference jumps out. We will reproduce it, trace it, find the line, fix it, and prove it is fixed.

**FAIL outlook_as_of, turn 3**

`output`
```text
FAIL  run_id=run-20261118-231305-c6b6 turn_id=outlook_as_of:t3
      tool=get_outlook params={'horizon_days': 5, 'as_of': '2026-11-14'}
      - as_of: expected 2026-11-13 got 2026-11-14
      expected call: get_outlook({'horizon_days': 5, 'as_of': '2026-11-13'})
                     [params are a subset match]
      actual call:   get_outlook({'horizon_days': 5, 'as_of': '2026-11-14'})
```

## The method

First, the method. The same seven steps, every time.

Reproduce it, alone. Read the YAML, and ask whether the test itself is right. Replay by hand to test one idea at a time. Open the trace and find the divergent call, the first place where something is wrong. Read the code at that step to find the root cause. Fix, then re run the thread and the whole suite. And write it down. These are the same seven steps as the lab guide.

**Seven steps, in order**

1. Reproduce: run it again, alone
2. Read the YAML: is the test itself right?
3. Replay by hand: test one idea per run
4. Open the trace: find the divergent call
5. Read the code at that step: the root cause
6. Fix, then re-run the thread and the whole suite
7. Write it down: symptom, cause, fix, proof

## Reproduce and read

Step one. Reproduce.

Run just this thread. Turn three fails. Run it again. Same result. The lab agent is scripted, so a failure is stable, and a stable failure is a gift. With a real model, if it only failed sometimes, I would run it ten times and count, before anything else.

**Same failure, every time**

`output`
*(output trimmed)*

```text
run_id=run-...  trace=.../traces/run-....jsonl
[thread] outlook_as_of  (outlook_as_of.yaml)
  PASS  turn_id=outlook_as_of:t1 tool=None
  PASS  turn_id=outlook_as_of:t2 tool=get_snapshot_date
  FAIL  turn_id=outlook_as_of:t3 tool=get_outlook
        - as_of: expected 2026-11-13 got 2026-11-14
  PASS  turn_id=outlook_as_of:t4 tool=get_outlook
  PASS  turn_id=outlook_as_of:t5 tool=get_bond_metrics
0/1 passed; FAILED: outlook_as_of
```

Step two, read the YAML, and check the test itself. In turn two, the user asked for the data date, the thirteenth. In turn three, they said as of that date. Nothing changed the anchor in between. So the expected date, the thirteenth, is correct. And the fourteenth is a partial load, which should never be used silently. The test is right. The agent is wrong.

**Is the test right?**

- t2: the user asks for the data date, 2026-11-13
- t3: "as of that date": nothing changed the anchor
- So as_of = 2026-11-13 is correct
- 2026-11-14 is a partial load: never a silent default

## Replay, then trace

Step three. Replay, to test one idea.

We did this in part two. At turn three, press e, and type the date explicitly. It passes. So the tool works and the data for the thirteenth exists. That rules out two suspects with one run. What is left is how the words that date get turned into a date.

**One idea per run**

- At t3, press e and type the date: 2026-11-13
- Result: PASS, rates -2.4 bp
- Rules out: the tool and the data
- Points at: how "that date" is resolved

Step four, open the trace for this turn, using the run ID from the first line of output. Read it top to bottom. State in has as of the thirteenth. The state was right going in. The decide tool generation outputs as of the fourteenth. That is the divergent call: the right date was in state, and was not used. The tool span then honestly returns data for the fourteenth: rates up one point seven. And state out still says the thirteenth.

**Step 4: the failing turn**

`output`
*(output trimmed)*

```text
TRACE 8735f504537b  turn_id=outlook_as_of:t3
  input: {"user": "Give me the 5-day outlook as of that date",
          "state_in": {"as_of": "2026-11-13", "latest_available": "2026-11-14", ...}}
  ├─ GENERATION decide_tool (model=scripted-rules)
  │    output: {"tool": "get_outlook",
  │             "params": {"horizon_days": 5, "as_of": "2026-11-14"}}
  ├─ SPAN tool:get_outlook
  │    output: {"as_of": "2026-11-14", "rate_change_bp": 1.7, "spread_change_bp": -0.6, ...}
  ├─ GENERATION compose_answer (model=scripted-rules)
  └─ OUTPUT {"answer": "5-day outlook as of 2026-11-14: rates 1.7 bp, ...",
             "state_out": {"as_of": "2026-11-13", ...}}
```

Now compare with a passing turn next to it. Turn four: and the twenty one day. Same state in. This time the decision uses the thirteenth. What is different? Not the state. The words. Turn three said that date. Turn four said nothing about a date. So the bug fires only when the user refers back to a date. That is a sharp clue, and we got it by putting two traces side by side.

**Compare: the next turn passes**

`output`
*(output trimmed)*

```text
TRACE 846e861fedbd  turn_id=outlook_as_of:t4
  input: {"user": "and the 21-day?",
          "state_in": {"as_of": "2026-11-13", "latest_available": "2026-11-14", ...}}
  ├─ GENERATION decide_tool (model=scripted-rules)
  │    output: {"tool": "get_outlook",
  │             "params": {"horizon_days": 21, "as_of": "2026-11-13"}}
  ├─ SPAN tool:get_outlook
  │    output: {"as_of": "2026-11-13", "rate_change_bp": -6.5, ...}
```

Put the evidence in one table. Memory: state in has the right date, fine. The tool: it returns exactly what it was asked for, fine. The data: the typed date passed in replay, fine. The decision step: it output the wrong date. That is where to look. Notice I have not opened the prompt, or blamed the model. The evidence pointed somewhere specific.

**The trace rules out three suspects**

| Suspect | Evidence in the trace | Verdict |
|---|---|---|
| Memory / state | state_in.as_of = 2026-11-13 | Fine |
| The tool | Returns exactly what it was asked for | Fine |
| The data | Typed date at t3 passes in replay | Fine |
| The decision step | decide_tool outputs 2026-11-14 | Divergent |

## Root cause

Step five. Read the code at that step.

The decision step is scripted decide, in agent dot py. Inside it, resolve as of turns words into a date. An explicit date always wins. But look at the next branch. If the user refers to a prior date, like that date or as of then, and drop carried is on, it returns latest available, the newest partial load, instead of state dot as of, the date the user anchored to. And outlook calls pass the flag, drop carried as of, which is set to true at the top of the file.

**The planted bug**

`python (shortened)`
```python
DROP_CARRIED_AS_OF = True          # planted bug (course exercise)
PRIOR_DATE_PHRASES = ("as of that date", "as of then", "that date", "same date")

def scripted_decide(text, state):
    def resolve_as_of(drop_carried=False):
        if explicit:
            return explicit.group(1)
        if refers_prior and drop_carried and state.latest_available:
            return state.latest_available      # wrong: newest partial load
        return state.as_of or tools.SNAPSHOT_DATE
    ...
    return "get_outlook", {"horizon_days": horizon,
        "as_of": resolve_as_of(drop_carried=DROP_CARRIED_AS_OF)}
```

Now every clue fits. Turn three says that date, and it is an outlook call, so the bug fires. Turn four has no date phrase, so it uses the stored date. Turn five says as of then, but it is a bond question, and bond calls do not pass the flag. And update state refuses to store the partial load date, so state out stays the thirteenth. One bad turn, then everything looks normal again. That is why it is easy to miss.

**Why only turn 3 breaks**

- t3 says "that date" and is an outlook call: bug fires
- t4 has no date phrase: uses state.as_of
- t5 says "as of then" but is a bond call: no flag passed
- update_state does not store the partial date: state_out stays 2026-11-13

Notice what I did not do. I did not rewrite the prompt. I did not blame the model. In a real model setup, this decision is made by the model and your code around it. The trace showed exactly which one. Without it, I could easily have spent a day tuning a prompt for a bug in a few lines of plain Python.

**I did not touch the prompt**

> **The trace pointed at plain Python**
> Without it, you could spend a day tuning the prompt for a bug in a few lines of code.

## Fix and prove

Step six. The fix, and the proof.

The fix is one line at the top of agent dot py: set drop carried as of to false. In real code you would delete the wrong branch, not keep a flag. The flag is only here so you can reset the exercise and try it again.

**The fix**

`python`
```python
DROP_CARRIED_AS_OF = False

# In real code: delete the branch, do not keep a flag.
# The flag exists so the exercise can be reset.
```

Re run the threads. All four cases pass, the journey scores five of five, and the exit code is zero. Now run pytest. Four tests fail, and that is correct. Each one asserts that the planted bug is there: that turn three fails, that the journey scores four of five, that the runner exits with one, and that the trace shows the wrong date. The bug they guard is gone. Read every red test before you call it a problem. Then undo the fix to put the exercise back.

**Re-run the threads and pytest**

`output`
```text
$ python day18_agent_testing/run_threads.py
  journey morning_check: 5/5 steps passed, required 5 -> PASS
4/4 passed                                   (exit code 0)

$ python -m pytest day18_agent_testing -q
FAILED tests/test_runner.py::test_planted_bug_is_detected_at_turn_3_only
FAILED tests/test_runner.py::test_almost_passing_journey_is_a_fail
FAILED tests/test_runner.py::test_main_exit_code_is_nonzero_on_failure
FAILED tests/test_runner.py::test_trace_tree_shows_the_divergent_call
4 failed, 13 passed
```

And then I open the new trace for turn three, and look at the parameter myself. As of the thirteenth. Rates minus two point four. I do not trust green alone. I want to see the value that was wrong, now right.

**The new trace for t3**

`output`
*(output trimmed)*

```text
├─ GENERATION decide_tool (model=scripted-rules)
│    output: {"tool": "get_outlook",
│             "params": {"horizon_days": 5, "as_of": "2026-11-13"}}
├─ SPAN tool:get_outlook
│    output: {"as_of": "2026-11-13", "rate_change_bp": -2.4, "spread_change_bp": 0.8, ...}
```

Step seven, write it down. Symptom: two red cases, both turn three, wrong date. Evidence: the trace shows the right state going in and the wrong date coming out of the decision step. Cause: resolve as of returns the partial load date for that date. Fix: the flag off, or in real code, the branch deleted. Proof: four of four cases pass, and the new trace shows the thirteenth. That is what you bring to a review. Not, one test failed and now it's fixed. This note, with a screen to back every line.

**The note you bring to a review**

| Field | What you write |
|---|---|
| Symptom | outlook_as_of:t3 and morning_check:t3: as_of 2026-11-14, expected 2026-11-13 |
| Evidence | Trace: state_in 2026-11-13, decide_tool 2026-11-14 |
| Cause | resolve_as_of returns latest_available for "that date" (DROP_CARRIED_AS_OF) |
| Fix | Flag off; in real code, delete the branch |
| Proof | 4/4 cases pass; new trace shows 2026-11-13 |

## TDD for agents

That loop, a red test first, then the fix, works for new features too. That is test driven development.

Red: write the thread first, and watch it fail. Green: make the smallest change that passes. With a real model, run it several times, because one pass is not proof. Run the whole suite, because a change can fix one thread and break three others. Then tidy up while the tests stay green.

**The loop, adapted for agents**

1. Red: write the thread first, and watch it fail
2. Green: the smallest change that passes
3. With a real model: run it several times
4. Run the whole suite: no regressions
5. Refactor while everything stays green

The lab ends with an exercise. Write a new thread, date switch. Anchor to the twelfth with a bond question. Switch to the thirteenth. Then ask: and the twenty one day outlook? Which as of should the last turn use? Write it down before you run it. That is the whole point of writing the test first: you decide what is right before the code tells you what it does.

**Write the thread that should have existed**

`yaml (your version)`
```yaml
thread: date_switch
turns:
  - user: "What is the OAS of POOL-A30 as of 2026-11-12?"
    expect_tool: get_bond_metrics
    expect_as_of: "2026-11-12"
  - user: "And its duration as of 2026-11-13?"
    expect_tool: get_bond_metrics
    expect_as_of: "2026-11-13"
  - user: "and the 21-day outlook?"
    expect_tool: get_outlook
    expect_as_of: ???              # write it down before you run it
```

The answer is the thirteenth, the latest date the user chose. Now the surprise. Run it against the buggy agent, and it passes. Why? This thread never asks for the data date, so the agent never learns the partial load date, and it never says that date. The buggy branch never runs. That is a useful test of date switching, but it does not guard this bug. So always run a new test against the broken version first. If it is green there, it is not protecting you from that bug.

**2026-11-13, and it passes even with the bug**

> **A test that cannot fail does not guard this bug**
> This thread never asks for the data date and never says "that date", so the buggy branch never runs.

And the rule that ties it together: every bug becomes a test, and that test stays forever. In the lab, outlook as of turn three is that test, and test runner dot py checks that the runner catches it. If anyone ever brings this bug back, the build goes red. Name the test after the behaviour it protects, so the next person knows why it exists.

**Every bug becomes a test**

- outlook_as_of:t3 is that test for this bug
- tests/test_runner.py checks the runner catches it
- Keep the test forever; it guards against the bug coming back
- Name it after the behaviour, not the ticket

Quick check. Pause and answer. A turn uses the wrong date, and your first idea is to rewrite the prompt. What should you do first? Open the trace. Check state in, the decision step's output and the tool span. Fix it where the value first goes wrong.

One more. After the fix, four pytest tests fail. Is the fix wrong? No. Read them. All four assert that the planted bug exists. They fail because it is gone. A red test is information, not a verdict. Read it before you react.

**Quick check:** After the fix, 4 pytest tests fail. Is the fix wrong?

<details><summary>Answer</summary>

No. Those 4 tests assert the planted bug exists. Read each one: they fail because the bug is gone.

</details>

Let's recap. Seven steps, from reproduce to write it down. Compare a failing turn with a passing one next to it. Find the divergent call: right state going in, wrong date coming out. Fix, re run, read every red test, and look at the new trace. And for test driven development: decide what is right first, and check that your test actually fails on the bug. Next: browser smoke tests, triage and release.

- Seven steps: reproduce, read, replay, trace, root cause, fix, write up
- Compare a failing turn with a passing one
- The divergent call: right state in, wrong date out
- Fix, re-run, read every red test, look at the new trace
- TDD: decide what is right first; check the test fails on the bug

The lab with the planted bug is linked in the description. Try to find it yourself, with the trace, before you look at the solution. If this helped, subscribe, and I will see you in the next video.

---

← [Day 18, Part 3](day18_p3.md) · [All lessons](README.md) · [Day 18, Part 5](day18_p5.md) →
