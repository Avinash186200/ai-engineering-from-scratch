# Day 18: Testing and debugging LLM agents

How to test a multi-turn agent that answers fixed-income and MBS questions by calling tools that return data as of a
snapshot date: write long conversations as YAML threads, check every turn's tool, arguments and `as_of` date, gate
user journeys on a strict pass threshold, trace every turn, and follow one failing turn from the test report to the
line of code that caused it.

| Video | Short |
|---|---|
| Day 18, full episode: coming soon | Why did the agent answer from the wrong date?: coming soon |

| File | What it is |
|---|---|
| [fi_agent/tools.py](fi_agent/tools.py) | Three fake, deterministic tools: snapshot date, 5/21-day outlook, bond metrics |
| [fi_agent/agent.py](fi_agent/agent.py) | The agent: conversation state, a scripted offline "LLM", an optional real-model mode, one planted bug |
| [fi_agent/tracing.py](fi_agent/tracing.py) | Trace, span and generation records to `traces/<run_id>.jsonl`; Langfuse too if configured |
| [run_threads.py](run_threads.py) | Runs every YAML thread and journey; PASS/FAIL per turn; `--thread`, `--replay` |
| [tests/threads/](tests/threads/) | Long-thread tests: expected tool, params (subset), `as_of`, grounded numbers per turn |
| [tests/journeys/morning_check.yaml](tests/journeys/morning_check.yaml) | A journey with `required: 5 of 5`: four out of five is a fail |
| [tools/show_trace.py](tools/show_trace.py) | Prints the trace tree for a `run_id`, or for one `turn_id` |
| [web/app.py](web/app.py) | A minimal chat page on the standard library |
| [tests/](tests/) | pytest: tools, runner, trace tree, and a Playwright smoke test (skipped if not installed) |
| [requirements.txt](requirements.txt) | PyYAML and pytest; the rest is optional |
| [LAB.md](LAB.md) | Seven steps: from a red test to the root cause and the fix |
| [SOLUTION.md](SOLUTION.md) | The debugging walk-through, step by step |

## Quick start
```bash
pip install -r day18_agent_testing/requirements.txt
python day18_agent_testing/run_threads.py
python -m pytest day18_agent_testing -q
```
`run_threads.py` exits 1 on purpose: one turn has a planted bug. pytest stays green because it asserts that the
runner catches it.

## Five lessons from a real production AI platform
1. The worst bugs gave a confident answer from the wrong date. Check the `as_of` argument on every tool call, not just the answer.
2. Single-question tests passed while long conversations broke. State carried across turns needs its own tests.
3. A journey that passes four steps out of five is still a broken journey for the person using it.
4. Every turn needs a `run_id` and a `turn_id` in its trace. Without them you cannot find the call that went wrong.
5. Replay the failing conversation turn by turn before you change code. Most fixes were one line once the divergent call was found.
