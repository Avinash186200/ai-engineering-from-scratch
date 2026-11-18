# Cheat sheet: how to show you understand a test case

Rule: no high-level explanations. Open it, point at it, run it.

## The checklist (in order, on screen)

- [ ] **Where it is defined.** Folder and file, e.g. `day18_agent_testing/tests/threads/outlook_as_of.yaml`. Start from the runner (`THREADS_DIR` and `JOURNEYS_DIR` in `run_threads.py`); don't search the whole disk.
- [ ] **What it is for.** One sentence. ("The date from turn 2 must carry over to turn 3.")
- [ ] **What it checks, per turn.** Read each field aloud: `expect_tool`, `expect_params` (a subset match), `expect_as_of`, `grounded_keys`.
- [ ] **Which run you are talking about.** The `run_id` from the first line of output (e.g. `run-20261118-231305-c6b6`) and the snapshot date. If results differ between runs, show both.
- [ ] **Replay by hand.** `python day18_agent_testing/run_threads.py --thread <name> --replay`. One turn at a time; press `e` to try different text. Note expected vs actual per turn.
- [ ] **Trace.** `python day18_agent_testing/tools/show_trace.py <run_id> --turn <turn_id>`. In production, the same trace in Langfuse, filtered by `run_id` and `turn_id`.
- [ ] **Entry point.** The file and function that received the message: `Agent.turn` in `fi_agent/agent.py`.
- [ ] **Divergent call.** The *first* generation or tool span that differs from what you expected. Show its input and output.
- [ ] **Root cause.** One or two sentences, pointing at code, prompt, state or data.
- [ ] **Cross-check (production).** The log line for the same request, e.g. in a Grafana dashboard.
- [ ] **Evidence.** Screenshots and links on the bug. Passing on replay? Screenshot it, post it.
- [ ] **Test coverage.** Does a test catch it? If a bug exists and the tests pass, add a test, and check that it fails on the bug.

## Per-turn check (long threads)

| Tool | Params | as_of | Grounded |
|---|---|---|---|
| `expect_tool`: right tool, or no tool? | `expect_params`: right values for the keys listed? | `expect_as_of`: the date the user anchored to; if none, the last complete snapshot, never a partial load | `grounded_keys`: each number in the answer comes from the tool output |

One failed turn fails the thread. A journey passes only if it reaches `pass_threshold` (`morning_check` needs 5 of 5).

## Numbers

- Thresholds and pass rates are gates for shipping, not reasons to stop looking. Name every failure.
- A wrong date or a wrong number is a hard fail, whatever the score.
- "Passed for me" is not an answer. Give run IDs and the difference.

## Process

- Findings -> bug description -> bug channel -> tracked bug -> fix PR. Never PR first.
- Test first (red), fix (green), full suite before push.
- Release: bump the version (never reuse a tag), run the suite, user acceptance testing, smoke test, production (with a go-ahead), smoke test again.

## Quick practice

```bash
python day18_agent_testing/run_threads.py
python day18_agent_testing/run_threads.py --thread outlook_as_of --replay
python day18_agent_testing/tools/show_trace.py <run_id> --turn outlook_as_of:t3
```

`outlook_as_of:t3` fails: `get_outlook` is called with `as_of: 2026-11-14` (the partial load) instead of `2026-11-13`,
the date carried from turn 2. `morning_check:t3` fails the same way (4/5, required 5). The cause is
`DROP_CARRIED_AS_OF = True` in `fi_agent/agent.py`. Walk through every line above for it.
