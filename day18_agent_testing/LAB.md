# Day 18 lab: find and fix a multi-turn agent bug

Run from the repo root. No API key needed: the agent uses a scripted offline "LLM", so every run gives the same result.

## Step 1: run the threads
```bash
pip install -r day18_agent_testing/requirements.txt
python day18_agent_testing/run_threads.py
```
Three threads and one journey run. Two fail, and the exit code is 1:

| Case | Result | Why |
|---|---|---|
| `bond_followup` | PASS | "its", "then" and "that one" resolve to the earlier bond and date |
| `explicit_dates` | PASS | An explicit date wins, follow-ups keep it, a data-date question re-anchors |
| `outlook_as_of` | FAIL at `t3` | `as_of: expected 2026-11-13 got 2026-11-14` |
| `morning_check` (journey) | FAIL, 4/5 | Same bug; the threshold is 5 of 5, so almost passing is a fail |

Note the `run_id` on the first line of output. You need it in Step 4.

## Step 2: read the YAML
Open `tests/threads/outlook_as_of.yaml`. Turn 2 asks for the data date (2026-11-13, five days old). Turn 3 says
"as of that date". The test expects `get_outlook` with `horizon_days: 5` and `as_of: 2026-11-13`.
Parameters are a subset match: only the keys you list are checked.

## Step 3: replay the conversation by hand
```bash
python day18_agent_testing/run_threads.py --thread outlook_as_of --replay
```
Press Enter for each turn and read the answer. At `t3` press `e` and type
`Give me the 5-day outlook as of 2026-11-13`. It passes. So the tool works, and the problem is how
"that date" is resolved.

## Step 4: open the trace
```bash
python day18_agent_testing/tools/show_trace.py <run_id> --turn outlook_as_of:t3
```
Read it top to bottom. `state_in` has `as_of: 2026-11-13`. The `decide_tool` generation outputs
`as_of: 2026-11-14`. That generation is the divergent call: the right date was in state and was not used.
2026-11-14 is `latest_available`, a partial load.

## Step 5: find the root cause
Open `fi_agent/agent.py` and read `resolve_as_of` inside `scripted_decide`. Find the branch that returns
`state.latest_available`, and the flag that switches it on for outlook calls.

## Step 6: fix and rerun
Make the one-line fix, then:
```bash
python day18_agent_testing/run_threads.py
python -m pytest day18_agent_testing -q
```
All four cases pass and the exit code is 0. Now pytest shows 4 failed: the four tests that assert the planted bug
exists (`test_planted_bug_is_detected_at_turn_3_only`, `test_almost_passing_journey_is_a_fail`,
`test_main_exit_code_is_nonzero_on_failure`, `test_trace_tree_shows_the_divergent_call`). That is correct: the bug
they guard is gone. Undo the fix to put the exercise back.

## Step 7 (exercise): add a thread that should have existed
Write `tests/threads/date_switch.yaml`: anchor to 2026-11-12, ask a bond question, switch to "as of 2026-11-13",
then ask "and the 21-day outlook?". Which `as_of` should the last turn use? Write it down before you run it.

## Optional extras
- Chat page: `python day18_agent_testing/web/app.py`, then open http://127.0.0.1:8018.
- UI smoke test: `pip install pytest-playwright`, then `python -m playwright install chromium`. Without these, the test is skipped.
- Real model: `pip install anthropic`, then set `ANTHROPIC_API_KEY` and `LAB_LLM=anthropic`. A real model may word
  its calls differently, so treat the threads as evals with a pass rate, not exact tests.
- Langfuse: `pip install langfuse` and set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` (and `LANGFUSE_HOST`).
  The local JSONL trace is always written as well.

## Where each test sits
```
     journeys (user goal, N of N steps)            few, strict
   threads (multi-turn: tool + params + as_of)
  runner and trace tests (pytest)
unit tests (tools, state)                          fast, many, exact
```
