# Day 15 lab: test an AI service properly

Run from the repo root. No API key needed.

## Step 1: run the whole suite
```bash
python -m pytest day15_testing -q
```
About 26 tests in four layers (most of the time is building the agent once):

| File | Layer | What it proves |
|---|---|---|
| `test_unit_tools.py` | Unit | The tools the LLM calls are correct: sorted, sized, caveat present, bad input is an error, not a crash |
| `test_properties.py` | Property (Hypothesis) | For hundreds of generated inputs: tools never crash, copied numbers are always grounded, emails are always redacted |
| `test_api_contract.py` | API contract | Status codes, response schema, validation (422), the SSE stream format, graceful degradation when the LLM is down |
| `test_llm_behaviour.py` | LLM behaviour | The right tool is called with the right arguments; the answer's numbers and funds come from the tool result |

## Step 2: break the code, watch a test catch it
Open `core/fund_model.py` and change `ascending=False` to `ascending=True` in `rank_funds`. Run the unit tests:
```bash
python -m pytest day15_testing/test_unit_tools.py -q
```
`test_ranking_is_sorted_and_sized` fails. Undo the change. A test you have never seen fail might not test anything.

## Step 3: let Hypothesis find a bug
In `day12_llmops/tracing.py`, weaken the email regex to `r"[a-z]+@example\.com"` and run:
```bash
python -m pytest day15_testing/test_properties.py -q
```
Hypothesis may still pass (its users are lowercase letters). Now change the strategy alphabet to include digits and run again:
the shrunk failing example appears, something like `0@example.com`. Undo both changes.

## Step 4: why we don't assert exact text
Look at `test_llm_behaviour.py`. It never checks the answer's wording. It checks which tool was called, the date argument,
that every number and fund in the answer exists in the tool result, and that the caveat survived.
Those properties hold for a fake model today and a real model tomorrow. Exact wording would not.

## Step 5: read the configs
- `pyproject_example.toml`: Ruff (including security rules), mypy strict, pytest markers (`llm`, `slow`), a coverage floor.
- `ci_testing.yml`: the pyramid in CI order: static checks, unit + property, API fuzzing with Schemathesis, then the eval gate.

## Step 6 (exercise): add a test that should have existed
Write a test that `/chat` never returns an API key or an email in its answer, even if the user's message contains one.
Hint: use `day12_llmops.guards.leaks_pii` on the response.

## The pyramid for AI apps
```
            evals (golden set, pass-rate gate)        slow, few, measure quality
        LLM behaviour (structure, grounding)
     API contract (schema, errors, fuzzing)
  unit + property (tools, parsing, validation)        fast, many, exact
static checks (ruff, mypy strict)                     seconds
```
