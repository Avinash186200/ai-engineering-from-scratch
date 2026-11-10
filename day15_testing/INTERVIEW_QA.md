# Interview questions: Testing AI services

For each question: open **Understand it** and read until it is clear, then say the **Answer** out loud in 30-45 seconds.
Code for the ideas is in this folder; the hands-on steps are in [LAB.md](LAB.md).


## Strategy

### 1. How do you test an LLM application when the output is non-deterministic?

<details><summary>Understand it</summary>

```text
SPLIT THE SYSTEM
An LLM app is mostly ordinary code around one non-deterministic call: tools, retrieval, prompt building, parsing, validation, API, storage. Test each kind differently.

1. DETERMINISTIC CODE (most of it): normal unit tests, exact assertions. Tools, parsers, formatters, guards.
2. PROPERTIES: rules that hold for all inputs ('never crashes', 'always returns valid JSON', 'never leaks an email'), checked with property-based testing (Hypothesis).
3. API CONTRACT: status codes, schemas, validation errors, streaming format; fuzz with Schemathesis.
4. LLM BEHAVIOUR WITH A STUB MODEL: did it call the right tool with the right arguments? Is the answer grounded in the tool result? Is the caveat present? Structure, not wording.
5. QUALITY WITH THE REAL MODEL: an eval suite (golden set) with a pass-rate threshold, run in CI or nightly. Accept that individual cases may vary; gate on the rate.
6. ONLINE: monitoring and guards in production (Day 12).

TECHNIQUES FOR NON-DETERMINISM
- temperature 0 / fixed seeds where supported (reduces, doesn't eliminate variation)
- assert on structured output (JSON schema) rather than prose
- run eval cases several times and use pass rates
- LLM-as-judge with a narrow rubric for open-ended answers
```

</details>

**Answer:** I split the system. Most of an LLM app is deterministic code, the tools, parsing, validation and API, which gets normal unit tests with exact assertions. On top of that I add property-based tests for rules that must always hold, contract tests and fuzzing for the API, and behaviour tests with a stub model that check which tool was called, with what arguments, and that the answer is grounded in the tool result, never the exact wording. Quality with the real model is measured by an eval suite with a pass-rate threshold in CI, and production has online monitoring.

### 2. What is the testing pyramid, and how does it apply to AI apps?

<details><summary>Understand it</summary>

```text
CLASSIC PYRAMID
Many fast unit tests at the bottom, fewer integration tests, a few slow end-to-end tests at the top. Fast feedback, cheap to run, easy to locate failures.

FOR AI APPS (bottom to top)
1. Static checks: lint (Ruff), types (mypy strict). Seconds.
2. Unit + property tests: tools, parsing, guards, prompt building. Seconds to a minute.
3. API contract and integration: real app in-process (TestClient), database in a container, schema fuzzing.
4. LLM behaviour with a stub model: tool routing, grounding, required content.
5. Evals with the real model: golden set, pass-rate gate. Minutes, costs money: run on PRs that touch prompts/models, and nightly.
6. Online monitoring and canary in production.

ORDER IN CI
Fail fast: cheap checks first, so a typo doesn't burn ten minutes of evals.

ANTI-PATTERN
'Ice-cream cone': everything tested by slow, flaky end-to-end chats with a real model. Expensive, flaky, and when it fails you don't know why.
```

</details>

**Answer:** The pyramid means many fast, precise tests at the bottom and a few slow broad ones at the top. For AI apps the bottom is static checks like Ruff and mypy strict, then unit and property tests for tools, parsing and guards, then API contract and integration tests, then LLM behaviour tests with a stub model, then evals with the real model on a golden set, and finally online monitoring. CI runs them in that order so cheap failures stop the pipeline early. The anti-pattern is testing everything through slow, flaky end-to-end chats with a real model.


## Unit and property tests

### 3. What do you unit test in an AI application?

<details><summary>Understand it</summary>

```text
THE TOOLS (highest value)
A tool bug becomes a confident wrong answer, because the model trusts the tool. Test: correct results on known inputs, sorting and sizes, edge cases (empty, one item, max), errors returned as data for bad inputs (bad date, weekend, out of range), required fields like caveats and as-of dates.

INPUT HANDLING
Date parsing, argument validation, type coercion (the LLM may send "5" instead of 5, or True), unknown enum values.

PROMPT BUILDING
The system prompt includes the right sections; retrieved chunks are inserted with source IDs; long histories are truncated correctly; untrusted content is wrapped/marked.

OUTPUT HANDLING
JSON parsing with repair/fallback, schema validation, citation extraction, formatting (0.0099 -> 0.99%).

GUARDS AND SECURITY
Redaction, PII detection, grounded-number checks, permission checks on tools.

STYLE
pytest, parametrize for many cases, fixtures for shared setup, fast (no network), one behaviour per test with a descriptive name.
```

</details>

**Answer:** The tools first, because a tool bug becomes a confident wrong answer: known inputs, sorting, edge cases, and bad inputs returned as error data instead of crashes, plus required fields like the caveat and as-of date. Then input handling, since LLMs send strings instead of numbers or unknown values; prompt building, that the right sections and source IDs go in and history truncates correctly; output parsing and schema validation; and guards like redaction and permission checks. I use pytest with parametrize and fixtures, with no network calls.

### 4. What is property-based testing? Why is it useful for AI systems?

<details><summary>Understand it</summary>

```text
EXAMPLE-BASED
You pick inputs and expected outputs: rank_funds('2025-06-19') returns 5 rows.

PROPERTY-BASED (Hypothesis in Python)
You state a rule that must hold for ALL inputs, and the library generates hundreds of inputs, including nasty ones: empty strings, unicode, huge numbers, negative values, boundary values. On failure it SHRINKS to the smallest failing input, which makes debugging easy.

GOOD PROPERTIES
- Never crashes; always returns a well-formed result (dict with 'error' or valid data).
- Round trips: parse(format(x)) == x.
- Invariants: output sorted; length <= top_n; probabilities sum to 1.
- Security: redact(text) never contains an email; output never contains a secret.
- Metamorphic: rephrasing or reordering input shouldn't change certain outputs.

WHY FOR AI
LLMs call tools with arguments nobody planned for. Users paste anything. Property tests explore that space systematically. The same idea applied to an HTTP API is Schemathesis: it generates requests from the OpenAPI schema.

DAY 15 LAB
test_rank_funds_never_crashes_and_is_well_formed: random text dates and integers; every result must be an error string or a valid ranking.
```

</details>

**Answer:** Instead of choosing examples, I state a rule that must hold for all inputs and a library like Hypothesis generates hundreds of cases, including edge cases like empty strings, unicode and huge numbers, and shrinks any failure to the smallest example. Good properties are 'never crashes and always returns a well-formed result', round trips, invariants like sorted output, and security rules like 'redacted text never contains an email'. It suits AI systems because LLMs and users send tools inputs nobody planned for. Schemathesis applies the same idea to HTTP APIs.

### 5. How do you mock the LLM in tests, and what are the risks of mocking?

<details><summary>Understand it</summary>

```text
WAYS TO MOCK
1. A fake model class with the same interface as the real adapter (FakeLLM): rule-based, deterministic. Best when you own the adapter interface.
2. Monkeypatch/patch the client call to return canned responses (unittest.mock, pytest monkeypatch).
3. Record/replay: record real responses once (VCR-style cassettes), replay in tests.
4. A local small model for integration tests.

WHAT MOCKS ARE GOOD FOR
Testing YOUR code paths: tool routing, the agent loop, retries, timeouts, fallback when the provider is down, parsing of odd responses (empty, malformed JSON, tool call with missing args), cost accounting.

RISKS
- The mock behaves better than the real model: tests pass, production fails.
- Interface drift: the provider's response format changes; the mock doesn't.
- False confidence about quality: a mock says nothing about answer quality.

MITIGATIONS
- Keep a contract test against the real API (small, nightly, marked 'llm').
- Evals with the real model for quality.
- Make the fake return nasty cases too (errors, malformed outputs).
```

</details>

**Answer:** I mock at the adapter interface with a deterministic fake model, or patch the client call with canned responses, or record and replay real responses. Mocks are great for testing my own code paths: tool routing, the agent loop, retries, timeouts, the fallback when the provider is down, and parsing malformed responses. The risks are that the mock behaves better than the real model, that the provider's format drifts away from the mock, and false confidence about quality. So I keep a small nightly contract test against the real API, evals with the real model, and make the fake return nasty cases too.


## API and integration

### 6. How do you test a FastAPI service?

<details><summary>Understand it</summary>

```text
IN-PROCESS WITH TestClient
from fastapi.testclient import TestClient; client = TestClient(app). Calls the app directly, no server or network. Fast and deterministic.

WHAT TO TEST
- Happy path: status 200 and the response matches the schema (Pydantic response_model).
- Validation: empty/too long/missing fields -> 422 with a useful message.
- Errors: dependency down -> a clean error or graceful fallback, never a stack trace to the user.
- Auth: no token -> 401, wrong role -> 403 (security day).
- Streaming: content-type text/event-stream, event order (status, tokens, done).
- OpenAPI: the schema lists the endpoints (clients and gateways rely on it).

DEPENDENCIES
Override with app.dependency_overrides (fake LLM, test database). For a real database: a Postgres container in CI (testcontainers or a service container) with migrations applied.

FUZZING
Schemathesis reads /openapi.json and generates many requests per endpoint, checking for 500s, schema violations and slow responses.
```

</details>

**Answer:** I use FastAPI's TestClient, which calls the app in-process with no server. I test the happy path against the response schema, validation errors returning 422, failures of dependencies returning a clean error or graceful fallback rather than a stack trace, auth with 401 and 403, the streaming content type and event order, and that the OpenAPI schema lists the endpoints. Dependencies are swapped with dependency overrides, a real Postgres runs in a CI container when needed, and Schemathesis fuzzes every endpoint from the OpenAPI schema looking for 500s and schema violations.

### 7. What is contract testing, and why does it matter when you expose models to other clients?

<details><summary>Understand it</summary>

```text
THE CONTRACT
What clients rely on: endpoint paths, request and response schemas, status codes, error format, auth, units and meanings of fields.

WHY IT MATTERS
Once an Excel add-in, a notebook, another team or an agent depends on your API, any change can silently break them: a renamed field, a percentage that becomes a decimal, a new required parameter.

HOW TO TEST IT
- Response models (Pydantic) as the source of truth; OpenAPI generated from them.
- Snapshot/diff the OpenAPI schema in CI: a breaking change (removed field, new required field, type change) fails the build unless the version is bumped.
- Schemathesis: generated requests must get responses that match the documented schema.
- Consumer-driven contracts (Pact) when there are many consumers.
- Example tests that pin units and meanings ('predicted_return is a decimal: 0.0099 = 0.99%').

VERSIONING
Additive changes are fine; breaking changes go to /v2 (models-as-a-product day).
```

</details>

**Answer:** The contract is what clients rely on: paths, request and response schemas, status codes, the error format, auth and the meaning and units of fields. When an Excel add-in, notebooks, agents or other teams use the API, a renamed field or a percentage turning into a decimal silently breaks them. So I make Pydantic models the source of truth, diff the generated OpenAPI schema in CI so breaking changes fail unless the version is bumped, fuzz responses against the schema with Schemathesis, and pin units with example tests. Breaking changes go to a new version.


## LLM behaviour and evals

### 8. How do you test an agent's tool use?

<details><summary>Understand it</summary>

```text
WHAT TO ASSERT
- Routing: question type -> expected tool (ranking question calls rank_funds; definition question doesn't).
- Arguments: the date/ID extracted correctly; types right; nothing invented.
- Sequence: multi-step plans call tools in a sensible order; no repeated identical calls (loops).
- Limits: step limit enforced; tool errors handled (returns error as data, model recovers or explains).
- Grounding: the final answer uses the tool result (numbers and entities present in it).
- Safety: tools with side effects need confirmation; unauthorised tools are never called.

HOW
- Unit level with a stub model (deterministic routing rules) to test the loop mechanics.
- With the real model: an eval set of (question -> expected tool + args) and measure tool-selection accuracy; run several times.
- From traces in production: tool success rate, steps per request.

EXAMPLE (Day 15 test_llm_behaviour.py)
'Which funds look best on 2025-06-19?' -> exactly one call, rank_funds, as_of = 2025-06-19.
```

</details>

**Answer:** I assert on routing, that a ranking question calls the ranking tool and a definition question doesn't; on arguments, that the date or ID is extracted correctly and nothing is invented; on sequence and limits, no loops and the step limit enforced; that tool errors are handled; that the final answer is grounded in the tool result; and that side-effecting or unauthorised tools aren't called. The loop mechanics are tested with a stub model; with the real model I measure tool-selection accuracy on an eval set over several runs, and in production I track tool success rate and steps per request.

### 9. How do you build and maintain an eval set (golden set)?

<details><summary>Understand it</summary>

```text
START
- 30-100 real or realistic questions covering the main intents, plus edge cases (bad dates, out-of-scope, ambiguous), plus safety cases (injection, PII requests).
- For each: the expected behaviour: the right tool and args, key facts that must appear, facts that must NOT appear, or a rubric.
- Sources: product requirements, UAT catalogues, real user questions (anonymised), and every production failure.

SCORING
- Deterministic checks where possible (tool called, number present, JSON valid).
- LLM-as-judge for open-ended answers with a narrow rubric, calibrated on human labels.
- Pass rate overall and per category.

IN CI
Run on every PR that touches prompts, models, tools or retrieval; block below a threshold (e.g. 90%); report per-category changes. Nightly with the real model.

MAINTAIN
- Every confirmed production failure becomes a case.
- Review quarterly: remove obsolete cases, rebalance categories.
- Keep it versioned in Git; don't train or tune prompts on the test portion only (keep a held-out slice).
```

</details>

**Answer:** I start with 30 to 100 realistic questions covering the main intents, edge cases and safety cases, each with expected behaviour: the right tool and arguments, facts that must and must not appear, or a rubric. Sources are requirements, a UAT catalog, anonymised real questions and every production failure. Scoring is deterministic where possible, with an LLM judge calibrated on human labels for open answers, reported overall and per category. It runs in CI on changes to prompts, models, tools or retrieval with a pass threshold, plus nightly with the real model, and it grows with every confirmed failure, versioned in Git with a held-out slice.

### 10. How do you deal with flaky tests in an AI codebase?

<details><summary>Understand it</summary>

```text
SOURCES OF FLAKINESS
- Real model calls in unit tests (non-deterministic, rate limits, network).
- Time: 'today', time zones, business days.
- Randomness without seeds; dict/set ordering assumptions.
- Shared state between tests (global agent, database not cleaned).
- Timing: sleeps, async races, timeouts.

FIXES
- No real model in unit tests: stubs; real model only in evals/marked tests.
- Freeze time (pass dates explicitly, freezegun), fixed seeds.
- Isolate state: fixtures with setup/teardown, transactions rolled back, restore patched globals in finally.
- Wait for conditions, not fixed sleeps.
- For evals: gate on pass RATE over the suite and repeated runs, not single cases.

POLICY
A flaky test is a bug. Quarantine it (mark, track), fix it within days. Never 'just re-run until green': it trains the team to ignore red builds.
```

</details>

**Answer:** Flakiness usually comes from real model calls in unit tests, time and time zones, unseeded randomness, shared state between tests, and timing races. I use stubs instead of real models outside the eval suite, pass dates explicitly or freeze time, fix seeds, isolate state with fixtures and restore anything I patch, and wait for conditions instead of sleeping. For evals I gate on the pass rate across the suite, not single cases. A flaky test is a bug: quarantine and fix it quickly, never re-run until green, because that teaches people to ignore red builds.


## Static checks and CI

### 11. Why use type checking (mypy strict) and linting (Ruff) in a Python AI project?

<details><summary>Understand it</summary>

```text
MYPY STRICT
- Catches whole classes of bugs before running: None where a value is expected (Optional misuse), wrong argument types, missing return values, typos in attribute names.
- Forces clear interfaces: tool signatures, adapter interfaces, Pydantic models. Helpful when an LLM-facing tool's arguments must be exact.
- Strict = no untyped functions, no implicit Any.

RUFF
- Very fast linter and formatter (replaces flake8, isort, black, many plugins).
- Catches unused imports and variables, undefined names, mutable default arguments, bare excepts.
- Security rules (bandit 'S'): hard-coded passwords, eval, subprocess with shell=True, insecure temp files.
- ASYNC rules: blocking calls inside async functions (a common cause of slow LLM servers).

WHY IN CI
Seconds to run, objective, no reviewer time spent on style. Fail the build on violations so the main branch stays clean.

EXTRA: STATIC IMPORT LINT
A rule that forbids importing vendor SDKs directly outside the adapter keeps the LLM layer vendor-neutral.
```

</details>

**Answer:** mypy strict catches whole classes of bugs before the code runs, like None where a value is expected, wrong argument types and attribute typos, and it forces clean interfaces for tools and adapters. Ruff is a very fast linter and formatter that catches unused or undefined names, mutable defaults and bare excepts, plus security rules like hard-coded secrets and shell=True, and async rules that catch blocking calls in async code. Both run in seconds in CI and fail the build, so reviewers don't spend time on style. A custom import lint can also stop anyone importing a vendor SDK outside the adapter.

### 12. What does a good CI pipeline for an AI service look like?

<details><summary>Understand it</summary>

```text
ON EVERY PULL REQUEST
1. Static: ruff check, ruff format --check, mypy strict. (seconds)
2. Unit + property tests with coverage. (under a minute)
3. API contract: start the app, Schemathesis fuzzing; integration tests against a Postgres container. (minutes)
4. Evals if prompts/models/tools/retrieval changed: golden set, threshold gate. (minutes, costs tokens)
5. Build the Docker image (proves it builds); scan dependencies/image for vulnerabilities.
6. Required checks + code review before merge (branch protection).

ON MERGE TO MAIN
Build and push the image tagged by commit; deploy to dev; smoke test; then the release process (Day 13).

NIGHTLY
Full evals with the real model, contract test against the provider API, dependency updates.

PRACTICES
Fail fast ordering; caching dependencies; secrets from the CI secret store; read the actual results after every push (don't assume green).
```

</details>

**Answer:** On every pull request: static checks first, Ruff and mypy strict, then unit and property tests with coverage, then API contract tests with Schemathesis fuzzing and integration against a Postgres container, then the eval gate if prompts, models, tools or retrieval changed, then building the image and scanning for vulnerabilities, all as required checks plus code review. On merge, build and push the image tagged by commit, deploy to dev and smoke test. Nightly, full evals with the real model and a contract test against the provider. And always read the actual CI results after a push.


## Scenarios

### 13. A prompt change passed all unit tests but broke production answers. What went wrong in your testing?

<details><summary>Understand it</summary>

```text
DIAGNOSIS
Unit tests with a stub model can't see prompt effects: the stub ignores the prompt. So a prompt change was effectively untested.

WHAT WAS MISSING
- An eval gate that runs on any PR touching prompts, with the real model, on a golden set that covers the broken behaviour.
- Grounding/quality checks in the eval (numbers must come from tools), not just 'answered something'.
- A canary in production with quality metrics (guard pass rate), so it would have been caught on 5% of traffic.
- Prompt versioning on traces, to see the cause quickly.

FIX
Roll back the prompt; add the failing cases to the golden set; require the eval job for prompt changes (CODEOWNERS / path filters in CI); canary prompt changes; alert on guard pass rate.
```

</details>

**Answer:** Unit tests with a stub model can't see prompt effects, because the stub ignores the prompt, so the change was effectively untested. What was missing was an eval gate with the real model that runs on any PR touching prompts, with grounding checks rather than 'it answered something', plus a canary in production watching the answer-quality pass rate and prompt versions on traces. The fix: roll back, add the failing cases to the golden set, make the eval job required for prompt changes via path filters, and canary prompt changes.

### 14. How would you test a RAG pipeline?

<details><summary>Understand it</summary>

```text
COMPONENTS AND TESTS
1. Ingestion/chunking (unit): chunk sizes and overlaps correct; tables and headings kept; metadata (doc id, page, date) attached; no empty chunks; idempotent re-indexing.
2. Embedding/indexing (integration): documents indexed with the right versions; deletes propagate; filters (date, permissions) work.
3. Retrieval (eval): for a set of questions with known relevant documents, measure recall@k / hit rate and MRR. Compare dense, keyword (BM25) and hybrid.
4. Generation (eval): faithfulness (answer supported by retrieved chunks), answer relevance, citation correctness. Ragas-style metrics or an LLM judge.
5. End to end: golden questions with expected key facts; 'I don't know' when the answer isn't in the corpus.
6. Security: permission filters (a user never retrieves another tenant's document); injected instructions inside documents are ignored.

KEY IDEA
Evaluate retrieval separately from generation: if retrieval misses, no prompt will fix it.
```

</details>

**Answer:** I test each stage. Chunking gets unit tests: sizes, overlap, metadata like document ID, page and date, no empty chunks, idempotent re-indexing. Indexing gets integration tests that versions, deletes and permission filters work. Retrieval gets its own eval: for questions with known relevant documents I measure recall at k and MRR, comparing dense, keyword and hybrid. Generation is evaluated for faithfulness, relevance and citation correctness, end to end with golden questions including ones where the right answer is 'I don't know', plus security tests that permissions hold and instructions inside documents are ignored. Retrieval and generation are evaluated separately, because no prompt fixes a retrieval miss.


## Glossary

| Term | Meaning |
|---|---|
| Testing pyramid | Many fast precise tests at the bottom, few slow broad ones at the top. |
| pytest fixture | Reusable setup (an app, a client, a database) injected into tests. |
| parametrize | Run one test function over many input cases. |
| Property-based testing | State a rule for all inputs; the library generates and shrinks cases (Hypothesis). |
| Shrinking | Reducing a failing generated input to the smallest one that still fails. |
| TestClient | FastAPI's in-process HTTP client for tests. |
| Contract test | Checks the promises an API makes to clients: schemas, codes, meanings. |
| Schemathesis | Generates requests from an OpenAPI schema to fuzz an API. |
| Stub / fake model | A deterministic stand-in for the LLM with the same interface. |
| Record/replay | Record real API responses once, replay them in tests. |
| Golden set | Curated eval cases with expected behaviour, run with a pass-rate gate. |
| Flaky test | Passes and fails without code changes; a bug to fix, not re-run. |
| mypy strict | Static type checking with no untyped code or implicit Any. |
| Ruff | Fast Python linter/formatter, including security (S) and async rules. |
| Coverage | Share of code executed by tests; a floor, not a goal. |
| recall@k / MRR | Retrieval metrics: was a relevant doc in the top k / how high was the first one. |
| Faithfulness | Answer supported by the retrieved context. |
