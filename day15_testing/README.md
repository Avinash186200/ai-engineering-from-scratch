# Day 15: Testing AI services

How to test an application whose core component is non-deterministic: test the deterministic parts exactly,
state properties that must hold for all inputs, lock down the API contract, check LLM behaviour by structure and
grounding instead of wording, and measure quality with evals.

| Video | Short |
|---|---|
| [Day 15, full episode](https://youtu.be/L3Sy2QjZFSI) | [How do you test an AI that answers differently every time?](https://youtube.com/shorts/621DD5uFK5c) |

| File | What it is |
|---|---|
| [conftest.py](conftest.py) | Shared pytest fixtures: the app loaded once, a test client |
| [test_unit_tools.py](test_unit_tools.py) | Unit tests for the tools, with parametrised bad inputs |
| [test_properties.py](test_properties.py) | Hypothesis property tests: never crashes, always grounded, always redacted |
| [test_api_contract.py](test_api_contract.py) | API contract: schema, 422 validation, SSE format, graceful degradation |
| [test_llm_behaviour.py](test_llm_behaviour.py) | Tool choice and arguments, grounded numbers and names, caveat present |
| [pyproject_example.toml](pyproject_example.toml) | Ruff (incl. security rules), mypy strict, pytest markers, coverage floor |
| [ci_testing.yml](ci_testing.yml) | The pyramid in CI: static, unit/property, Schemathesis fuzzing, eval gate |
| [LAB.md](LAB.md) | Six steps, including breaking the code to watch a test catch it |
| [INTERVIEW_QA.md](INTERVIEW_QA.md) | Interview questions with full explanations and spoken answers |

## Quick start
```bash
python -m pytest day15_testing -q
```

## Five lessons from a real production AI platform
1. Most bugs that reached users were in ordinary code around the model: tools, parsing, config. Test those exactly.
2. Property tests and API fuzzing find the inputs nobody thought of, which is exactly what LLMs send to tools.
3. Strict types and lint in CI are cheap and catch whole classes of bugs before review.
4. Never assert exact LLM wording. Assert tool calls, grounding, schema and required content.
5. Read the actual CI results after every push. A whole repo was red for a missing secret, and nobody looked.
