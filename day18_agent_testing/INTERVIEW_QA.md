# Interview questions: Testing and debugging agents

For each question: open **Understand it** and read until it is clear, then say the **Answer** out loud in 30-45 seconds.
Code for the ideas is in this folder; the hands-on steps are in [LAB.md](LAB.md). Short-form questions on the same
topic are in [`interview_bank/agent_testing.md`](../interview_bank/agent_testing.md).


## Test design

### 1. How would you structure the tests for an agent that answers questions through data tools?

<details><summary>Understand it</summary>

```text
THREE KINDS OF CASE
1. SINGLE-TURN: one question, one answer. Tool choice, arguments, grounding.
2. MULTI-TURN / LONG THREADS: many turns in one session. Memory: a date or ID set early must still be used later.
   One failed turn fails the thread, so thread pass rates look low.
3. JOURNEYS: one full analyst task, step by step, with a check per step.

WHAT EACH TURN CHECKS
- expected tools        e.g. get_snapshot_date, get_outlook
- expected arguments    e.g. horizon_days: 21, as_of: the snapshot date
- answer checks         must contain / must not contain / number range / judge rubric

WHY YAML
Cases are data, the runner is code. People who don't write Python can read and add cases.

THRESHOLDS
golden pass = target, minimum pass = release gate. Clearing the gate does not explain the failures below 100%.
```

</details>

**Answer:** I split the cases into single-turn tests, long multi-turn threads and journeys that follow a full analyst task. Each case is a YAML file: per turn, the user message, the tools it should call, key arguments like `as_of`, and checks on the answer. The runner is code, the cases are data, so people outside engineering can add them. The suite has a golden pass target and a minimum pass gate, and I still name the cause of every failure even when the gate is cleared.

### 2. Why do long threads catch bugs that single-turn tests miss?

<details><summary>Understand it</summary>

```text
CONTEXT CARRY-OVER (lab thread outlook_as_of)
Turn 2: "What date is the data? Is it fresh?"        -> get_snapshot_date   (2026-11-13; partial load 2026-11-14)
Turn 3: "Give me the 5-day outlook as of that date"  -> get_outlook(horizon_days=5, as_of=2026-11-13)  <- must carry over
Turn 4: "and the 21-day?"                            -> get_outlook(horizon_days=21, as_of=2026-11-13)

Each turn alone looks fine: the turn-3 words sent to a fresh agent give the right date.
The bug only shows when turn 3 needs the date from turn 2.

COMMON CAUSES
- history trimming drops tool results before user messages
- the prompt never tells the model to reuse the as_of
- the tool has a default (today, or the newest partial load) that hides a missing argument
- the date resolver picks the newest load instead of the date the user anchored to (the lab's planted bug)

SCORING
A thread passes only if every turn passes. 6 of 10 threads passing can be a good result.
```

</details>

**Answer:** Because many bugs are about memory, not about one answer. In a thread, turn 3 may need a date set in turn 2; each turn looks fine alone, and the bug only shows when the value has to carry over. Typical causes are history trimming that drops tool results, a prompt that doesn't ask the model to reuse the date, and tool defaults that hide a missing argument. Because one failed turn fails the whole thread, I read thread pass rates in context and break failures down by turn.

### 3. How do you test tool-calling behaviour, not just the final text?

<details><summary>Understand it</summary>

```text
FOUR LAYERS
1. Selection   right tool?                     exact check on the tool name
2. Arguments   right IDs, dates, horizons?     exact check on arguments
3. Use         numbers in the answer = numbers in the tool result?   groundedness check
4. Answer      correct, complete, clear?       judge with a narrow rubric

ALSO CHECK
- no unneeded tool calls (cost, latency)
- tool errors handled: the agent says what failed, doesn't invent a value
- empty results: "not available", not a guess
```

</details>

**Answer:** I check four layers: the right tool, the right arguments, faithful use of the tool result, and a correct final answer. The first three get exact checks against the trace; only the wording goes to a judge. I also check the agent doesn't call tools it doesn't need, handles tool errors honestly, and says data is unavailable instead of guessing.

### 4. What makes as-of dates a special testing concern?

<details><summary>Understand it</summary>

```text
SNAPSHOT DATA
The lab tools return data as of a snapshot date, not live. Calling it "today's" data is a wrong answer in finance.
In the lab: 2026-11-13 is the last complete snapshot (5 days old, not fresh); 2026-11-14 is a partial load.

TESTS
- "What date is your data?"  -> quotes the snapshot date from get_snapshot_date
- "Is it fresh?"             -> says how old the snapshot is, says stale if stale, mentions the partial load
- run once with a stale snapshot on purpose
- every later tool call passes the same as_of

SILENT FAILURE
If as_of is missing or wrong (today, or a partial load), the tool still returns numbers. Nothing crashes. Only an
argument check or a date check in the answer catches it.
```

</details>

**Answer:** The tools return data as of a snapshot date, so the agent must quote that date and say honestly whether it's fresh. I test the date question, the freshness question, a deliberately stale snapshot, and that every later tool call passes the same `as_of`. The danger is that a missing or wrong `as_of` fails silently: the tool still returns numbers, for today or for a partial load, so only an argument check catches it.


## Debugging

### 5. Take me through debugging a multi-turn test that fails.

<details><summary>Understand it</summary>

```text
1. FIND      turn_id in the report (e.g. outlook_as_of:t3) -> the runner's test folder -> the YAML file
2. READ      say what each turn asks and expects
3. LOCATE    which turn, which check failed (run output)
4. REPLAY    type the same turns by hand in a fresh session
5. TRACE     entry point -> generation for that turn -> tool span: name, arguments, result
6. CAUSE     first wrong step = cause; everything after = symptom
7. RECORD    bug with steps, trace link, screenshot; add a test if none covers it

LAB EXAMPLE (outlook_as_of:t3)
Run output:  - as_of: expected 2026-11-13 got 2026-11-14
Replay:      typing "as of 2026-11-13" at t3 passes -> the tool and the data are fine
Trace:       state_in.as_of = 2026-11-13; GENERATION decide_tool outputs as_of = 2026-11-14  <- divergent call
Cause:       fi_agent/agent.py, resolve_as_of: with DROP_CARRIED_AS_OF = True, "that date" on an outlook
             call returns latest_available (the partial load) instead of the carried as_of.
Fix:         DROP_CARRIED_AS_OF = False -> 4/4 cases pass.
```

</details>

**Answer:** I find the YAML from the test ID and read each turn out loud. I find the failing turn and check, then replay those turns by hand in a fresh session. In the trace I go from the entry point to that turn's tool span and look at the tool, the arguments and the result. The first wrong step is the cause. In the lab thread, turn 3 calls `get_outlook` with `as_of` 2026-11-14, the partial load, instead of 2026-11-13 from turn 2. The trace shows the right date in state going in and the wrong date coming out of the decision step, which points at one flag in the date resolver. Then I write the bug with steps, trace link and screenshot, and add a test if one is missing.

### 6. What does a trace tool give you that logs don't?

<details><summary>Understand it</summary>

```text
TRACE       one request end to end
SPAN        one step: tool call, retrieval, guard
GENERATION  one LLM call: prompt, output, model, tokens, cost

LOGS                                  TRACE TOOL (e.g. Langfuse)
lines of text                         tree per request, grouped by session
join turns by grep and timestamps     every turn of a thread side by side
prompt often not logged               exact prompt and history per call
                                      tokens and cost per generation

METRICS (e.g. Grafana): error rate, latency, tool failures over time. Spot with metrics, explain with traces.
```

</details>

**Answer:** A trace tool groups one request into a tree: spans for tool calls and generations for model calls, with the exact prompt, arguments, results, tokens and cost, and it links every turn of a session. With logs I'd be joining lines by timestamp and the prompt often isn't there. I use metrics in Grafana to spot a problem across many requests and the trace to explain one.

### 7. A teammate reports every test passing; your run shows two failures. How do you resolve it?

<details><summary>Understand it</summary>

```text
DIFF THE SETUPS
commit | model version | prompt version | snapshot date | seed | config | test set version

THEN
- replay the two failures on both setups
- run each 5 times: always fails / sometimes / never

OUTCOMES
setup difference -> pin it, document it
flaky            -> report the pass rate, fix the cause or tighten the check
real bug         -> bug + trace + test

NOT AN ANSWER
"It passed for me." A threshold pass is not "all passed" either.
```

</details>

**Answer:** I treat the difference as a bug. We share run files and diff commit, model, prompt version, snapshot date, seed and config. Then I replay the two failures on both setups and repeat each a few times. Either it's a setup difference, a flaky case with a measured pass rate, or a real bug that gets a report, a trace and a test.


## Reliability

### 8. How do you keep agent tests trustworthy when model output varies?

<details><summary>Understand it</summary>

```text
REDUCE    temperature 0, fixed seed where supported (reduces, does not remove variation)
REPEAT    run important cases k times, report pass rate
METRIC    pass@k = at least one of k passes  (can it ever?)
          all-k-pass = every one passes      (is it reliable?)  <- what users feel
CHECKS    exact checks on tools and arguments; judge only for wording
NEVER     rerun until green
```

</details>

**Answer:** I lower randomness with temperature 0 and a fixed seed where supported, but I don't rely on it. Important cases run several times and I report a pass rate. For a user-facing chat I care about all-k-pass more than pass@k, because one bad answer in five is a problem. Exact checks cover tools and arguments, a judge covers only wording, and I never rerun until green.

### 9. When should you trust an LLM judge?

<details><summary>Understand it</summary>

```text
KNOWN BIASES
- prefers longer answers
- prefers its own style
- misses a wrong number that sounds right
- varies between runs

SAFE USE
- narrow rubric, one question per judge call
- pin judge model and prompt
- facts, numbers, dates on exact checks
- measure agreement with human labels on a sample; re-check when the judge changes
```

</details>

**Answer:** Only for what exact checks can't cover, like tone and completeness, and only after I've measured its agreement with human labels. Judges prefer long answers and their own style, miss confident wrong numbers and vary between runs. So numbers and dates stay on exact checks, the rubric is narrow, and the judge model and prompt are pinned.

### 10. Playwright or Selenium for end-to-end chat tests, and why?

<details><summary>Understand it</summary>

```text
PLAYWRIGHT                                   SELENIUM
auto-waits for elements                      explicit waits, more flaky sleeps
Chromium, Firefox, WebKit                    all browsers through drivers
trace viewer, screenshots, video built in    add-ons
works with the DOM, not pixels               works with the DOM
newer, smaller ecosystem                     huge ecosystem, long history

For a streaming chat UI the auto-waiting matters most.
```

</details>

**Answer:** Playwright for a new chat UI. It waits for elements by itself, which matters when replies stream in, and has tracing, screenshots and video built in across Chromium, Firefox and WebKit. Selenium still works and has a bigger ecosystem, but needs more waiting code and tends to be flakier here.


## Process and release

### 11. How do bugs, tests and fixes fit together in your workflow?

<details><summary>Understand it</summary>

```text
ORDER
1. bug report: steps, expected vs actual, trace link, versions, snapshot date, screenshot
2. failing test that reproduces it  (test-driven: red first)
3. fix
4. full regression suite
5. comment on the bug: passing, with screenshot

CHECK THE MAPPING
All tests green but bugs still open -> the suite is missing cases.

TRIAGE
One board. Label: agent / tool / data / test / infra. Owner per item. Repeats grouped.
```

</details>

**Answer:** Bug first, then a failing test, then the fix, then the full regression suite, then a comment on the bug with the result. Every bug maps to a test, so if the suite is green while bugs are open, the suite is missing cases. Failures from tests, UAT and users go to one triage board, labelled agent, tool, data, test or infra, each with an owner.

### 12. What has to happen before an agent version reaches production?

<details><summary>Understand it</summary>

```text
1. freeze version; prompts and tool schemas are part of it
2. full regression suite; compare with thresholds AND last release
3. cost and latency vs baseline (tokens per turn, p95)
4. unique tag (never reuse a tag already on an old commit; bump instead)
5. deploy to UAT -> smoke test
6. deploy to production -> smoke test
7. rollback ready

SMOKE TEST: up? basic question? right snapshot date? one tool call end to end? traces arriving?
```

</details>

**Answer:** I freeze the version, including prompts and tool schemas, run the full regression suite and compare with both the thresholds and the last release, including cost and latency. The tag must be unique; if it already points at an old commit I bump the version. Then UAT with a smoke test, production with another smoke test, and rollback ready.

### 13. How do you grow a test corpus over time?

<details><summary>Understand it</summary>

```text
SOURCES   expert questions | public questions | synthetic variants | production failures
METHOD    a few seed questions -> generate similar wordings -> curate
GOLDEN    small set with checked answers (e.g. ~70 of 2,500)
SCRAPING  terms of use, robots rules, licence, no personal data, keep source URL, tag and filter
OWNERS    YAML template so analysts can add cases; review them like code
```

</details>

**Answer:** From four sources: expert questions, real public questions, synthetic variants generated around seed questions, and every production failure. A small curated golden set has checked answers. When scraping I respect terms, licences and robots rules, avoid personal data and keep the source of every question. A YAML template lets analysts add cases, which we review like code.


## Glossary

| Term | Meaning |
|---|---|
| Long thread | A multi-turn test with many turns; one failed turn fails the thread. |
| Journey | A test that follows one full analyst task, with a check per step. |
| Golden pass / minimum pass | Target pass count / release gate for a suite. |
| as_of | The snapshot date a data tool reads from. |
| Trace / span / generation | One request / one step / one LLM call. |
| Groundedness | Every claim in the answer comes from a tool result or document. |
| pass@k | At least one of k runs passes. |
| Smoke test | A few-minute check that a deployment works end to end. |
