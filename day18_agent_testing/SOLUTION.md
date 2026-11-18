# Day 18 solution: the dropped as_of

Read this after you have tried [LAB.md](LAB.md).

## 1. Find the failing test
`python day18_agent_testing/run_threads.py` prints:
```
FAIL  run_id=... turn_id=outlook_as_of:t3 tool=get_outlook params={'horizon_days': 5, 'as_of': '2026-11-14'} as_of=2026-11-14
      - as_of: expected 2026-11-13 got 2026-11-14
      expected call: get_outlook({'horizon_days': 5, 'as_of': '2026-11-13'})  [params are a subset match]
      actual call:   get_outlook({'horizon_days': 5, 'as_of': '2026-11-14'})
```
The journey `morning_check` fails at the same step and scores 4/5 against a threshold of 5.

## 2. Read the YAML
Turn 3 of `tests/threads/outlook_as_of.yaml` expects the date the user anchored to in turn 2 (2026-11-13).
The tool name and the horizon are right. Only the date is wrong, so the answer reads fine and is still wrong.

## 3. Replay
With `--replay`, typing the date explicitly at `t3` passes. The tool and the data are fine. The fault is in
resolving "that date".

## 4. Open the trace
`python day18_agent_testing/tools/show_trace.py <run_id> --turn outlook_as_of:t3`:
- `input.state_in.as_of` is `2026-11-13`: state is correct going in.
- `GENERATION decide_tool` outputs `as_of: 2026-11-14`: this is the divergent call.
- `SPAN tool:get_outlook` returns numbers for 2026-11-14 (rates 1.7 bp instead of -2.4 bp).
- `state_out.as_of` is still `2026-11-13`, which is why turn 4 passes again. Only one turn breaks, which makes it easy to miss.

## 5. Root cause
In `fi_agent/agent.py`, `scripted_decide` resolves the date for outlook calls with
`resolve_as_of(drop_carried=DROP_CARRIED_AS_OF)`. With the flag on, a reference to a prior date returns
`state.latest_available` (the newest partial load) instead of `state.as_of` (the carried-over date).
Bond questions do not pass the flag, which is why turn 5 ("as of then") is fine.

## 6. Fix
One line at the top of `fi_agent/agent.py`:
```python
DROP_CARRIED_AS_OF = False
```
In real code you would delete the branch, not keep a flag. The flag is here so the exercise can be reset.

## 7. Rerun
```bash
python day18_agent_testing/run_threads.py      # 4/4 passed, exit code 0
python -m pytest day18_agent_testing -q
```
`test_after_the_fix_everything_passes` already proves the fix (it switches the flag off inside the test).
The four tests that assert the bug exists now fail on purpose (`test_planted_bug_is_detected_at_turn_3_only`,
`test_almost_passing_journey_is_a_fail`, `test_main_exit_code_is_nonzero_on_failure`,
`test_trace_tree_shows_the_divergent_call`). Undo the fix to restore the lab.

## What to take away
- Assert the arguments of the tool call, especially dates. The wording of the answer told you nothing here.
- The bug showed only in a conversation: the same question with an explicit date passed.
- The trace showed correct state going in and a wrong call coming out. That points to the decision step, not the tool.
