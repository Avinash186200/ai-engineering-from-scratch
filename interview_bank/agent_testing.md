# Agent testing and debugging

Code to back these answers: `day18_agent_testing/` (YAML threads, the runner, and the lab tools `get_snapshot_date`,
`get_outlook(horizon_days, as_of)` and `get_bond_metrics(bond_id, as_of)`). Hands-on steps: `day18_agent_testing/LAB.md`.

### 1. What is the difference between a single-turn and a multi-turn test?
A single-turn test sends one question and checks one answer. A multi-turn test sends several turns in one
conversation, and later turns depend on earlier ones. So it also tests memory: if turn 2 sets a date, turn 3 must
still use it.

### 2. What is a long-thread test?
A multi-turn test with many turns, often eight or more, that copies a real analyst session. One failed turn fails
the whole thread. So a thread pass rate looks low: six of ten threads passing can be a good result.

### 3. Where are your tests defined, and how do you find one you don't know?
In YAML files under a tests folder. If I don't know where, I don't guess. I grep for the test ID or a line of the
question, then read the runner to see which folder it loads. I can go from a report line to the file in a minute.

### 4. What goes into a YAML test case for an agent?
An ID, tags, and the turns in order. Each turn has the user message, the tools it should call, key arguments such
as `as_of`, and checks on the answer: must contain, must not contain, a number range, or a judge rubric.

### 5. Why keep tests in YAML rather than only in code?
So people who don't write Python can read and add cases. An analyst or product person adds a file; the runner
stays the same. The test set grows faster and reflects real questions.

### 6. What is a journey test?
A test that follows one full task the way an analyst does it: pick a segment, pick a model, set a date, use their
usual shortcuts. Every step has its own check, so a failure points at the exact step.

### 7. What do golden pass and minimum pass mean?
Two thresholds on a suite. Golden pass is the target; below minimum pass the release is blocked. Passing at 26 of
28 clears a golden pass of 26, but two tests still failed, and each needs a named cause.

### 8. What does as-of mean for data tools?
The tools return data from a snapshot date, not live data. The agent must quote that date and must not call old
data today's. Asked whether data is fresh, it compares the snapshot date with today and says so plainly.

### 9. What are a trace, a span and a generation?
A trace is one request end to end. A span is one step inside it, such as a tool call or retrieval. A generation is
a span for one LLM call, with the prompt, output, model, tokens and cost.

### 10. Why use LLM tracing such as Langfuse instead of plain logs?
Logs are lines of text that are hard to join across turns. A trace tool groups every turn, tool call, argument,
tool result and prompt under one session. From a failed test you click straight to what the agent actually did.

### 11. What is Grafana for in an agent system?
Metrics and logs over time: error rate, latency, tool failures, tokens. Grafana tells you something is wrong
across many requests. The trace tool explains one request. Use the first to spot, the second to explain.

### 12. What does testing a thread manually mean?
Opening the chat and typing each turn yourself, in order, in a fresh session, then watching the answers and the
trace. Running the automated suite is not manual testing. If you haven't done it, say no, and say when you will.

### 13. How much domain knowledge does an agent tester need?
Enough to tell a right answer from a wrong one. If you don't know what a coupon or a horizon is, you can't judge
the output. A quick start: list every question in the suite, group them, and build a glossary of unknown terms.

### 14. Walk me through how you'd debug a failing multi-turn test.
Open the YAML from the test ID and read each turn. Find the failing turn and check in the run output. Replay the
turns by hand in a fresh session. Open the trace for that turn: entry point, tool called, arguments, tool result,
model output. Find the first wrong step; that is the cause. In the lab, turn 3 of `outlook_as_of` calls
`get_outlook` with `as_of` 2026-11-14, the partial load, instead of 2026-11-13 from turn 2. The trace shows the
right date in `state_in` and the wrong one in the `decide_tool` output; the cause is `DROP_CARRIED_AS_OF` in
`fi_agent/agent.py`. Write the bug with steps, trace link and
screenshot, and add a test if none covers it.

### 15. How do you evaluate an agent that calls tools?
Four layers: did it pick the right tool, pass the right arguments, use the tool result faithfully, and give a
correct, useful answer. Tool names and arguments get exact checks. Wording gets a judge. Also check it skips tools
it doesn't need and handles tool errors.

### 16. What can go wrong with LLM-as-judge?
The judge can be wrong, prefer long answers, prefer its own style, miss a wrong number that sounds right, and
change its mind between runs. Keep facts and numbers on exact checks, pin the judge model and prompt, and measure
its agreement with human labels on a sample.

### 17. What is groundedness and how do you test it?
Every claim in the answer comes from a tool result or document, not model memory. Compare each number in the
answer with the tool output in the trace. Also ask questions where the tool returns nothing: the right answer is
that the data is not available.

### 18. How do you test freshness and as-of behaviour?
Ask what date the data is as of, and whether it is fresh. Check the answer quotes the snapshot date. Run once with
a stale snapshot on purpose. Then check every later tool call in the thread passes the same `as_of`, because that
is where multi-turn breaks most often.

### 19. A test passes for you and fails for a colleague. What do you do?
Treat the gap as a bug. Compare both runs: commit, model version, prompt version, snapshot date, seed, config. Then
replay the failing cases on both setups. "It passed for me" is not an answer; two run files side by side are.

### 20. How do you handle nondeterminism and flaky tests?
Reduce randomness with temperature 0 and a fixed seed where supported, knowing it doesn't remove it. Run important
cases several times and report a pass rate. A case that passes 3 of 5 is flaky: fix the cause or tighten the
check. Never rerun until green.

### 21. What is pass@k, and when is it the wrong metric?
pass@k is the chance at least one of k tries passes. It answers whether the agent can ever do the task. For a
user-facing chat you care whether it passes every time, so measure all-k-pass. One bad answer in five is a
problem.

### 22. What is a regression suite for an agent?
A fixed set of tests run before every push and release. Every fixed bug becomes a test in it. Results are compared
with the last good run, not just a threshold, so an old behaviour breaking shows up at once.

### 23. How should bugs and tests relate?
Every bug maps to at least one test. If all tests pass while a bug is still open, the tests are missing something:
add a case that fails because of the bug. Post the replay result on the bug, reproduced or passing, with a
screenshot.

### 24. Playwright or Selenium for testing a chat UI?
Playwright for a new project. It waits for elements by itself, so fewer flaky sleeps; drives Chromium, Firefox and
WebKit; and has tracing, screenshots and video built in. Selenium still works and has a huge ecosystem, but needs
more waiting code for a streaming chat UI.

### 25. What does test-driven development look like for an agent?
Write the YAML case first and run it: it fails, which proves the test can fail. Build the feature until it passes.
Then run the whole suite to check nothing else broke. Commit history shows red, then green.

### 26. Is breaking a test on purpose the same as explaining a real failure?
No. A planted break shows the test can catch a fault. It says nothing about why a real run failed. When asked
about two real failures, explain those two, from their run output and traces.

### 27. What goes in a bug report for an agent?
The test ID or exact turns, expected versus actual, the trace link, model and prompt versions, the snapshot date, a
screenshot, and your best guess at the cause. One bug per report. Someone else should reproduce it from the report
alone.

### 28. How do you use a trace to separate cause from symptom?
Start at the top span, the entry point, then walk down the failing turn span by span. The first wrong thing is
usually the cause, for example a tool call missing `as_of`. Everything after it, like a wrong date in the answer,
is a symptom.

### 29. How do you build a test corpus from scratch?
Mix expert questions, real public questions and synthetic ones. Start with a few seed questions and generate
similar wordings around each. Then curate a small golden set with checked answers, for example about 70 out of
2,500.

### 30. What are the risks of scraping public questions for a corpus?
Terms of use, robots rules, licences, and personal data. Keep the source URL for each question. Clean and tag
them: many public questions come from outside customers and don't sound like an analyst. An LLM can do the first
pass, a human checks a sample.

### 31. How do you run triage for agent failures?
One board or channel for every failure, from tests, UAT or users. Label each as agent, tool, data, test or infra,
and give it an owner. Group repeats. Turn new failure types into new tests. Fixes come after the bug is written
up.

### 32. Walk me through releasing a new agent version.
Freeze the version, run the full regression suite, compare with thresholds and the last release, and tag it. Tags
must be unique: if a release-candidate tag already points at an old commit, bump the version. Deploy to UAT, smoke
test, deploy to production, smoke test again, and keep rollback ready.

### 33. What is in a smoke test for an agent?
Is it up, does it answer a basic question, does it report the right snapshot date, does one tool call work end to
end, and do traces arrive. A few minutes, not the full suite.

### 34. Why is a prompt change a release?
It changes behaviour as much as code does. A small wording change can break tool choice or date handling. So
prompts live in version control, every change runs the regression suite, and each trace records the prompt
version.

### 35. A tool's schema changes. What do you do?
Find every test that uses the tool and update its expected arguments. Run the suite and watch for the agent still
sending the old field. Add a case for the new field, version the schema, and keep the old field working while older
callers move.

### 36. How do you catch cost and latency regressions?
Track tokens, cost and latency per test and per turn, and compare with the last baseline. A prompt that passes
every test but doubles tokens is still a regression. Set a budget and fail the build when it is clearly exceeded.

### 37. Six of ten long threads pass. Is that bad?
Not by itself. When one failed turn fails the thread, 60 percent can be good. Look at the trend and at which turn
positions fail. The same few causes usually repeat; fix them and many threads turn green.

### 38. You report all passing and your lead's run shows two failures. What now?
Don't argue. Share your run file and ask for theirs. Diff the setups, then replay the two failures by hand and in
the trace. Either you find the cause or you show the case is flaky with a measured pass rate.

### 39. How do you get non-engineers adding test cases?
Show one YAML case, explain each field in plain words, and give a template. Let them add one while you watch, run
it together, then review their cases like code.

### 40. What separates a strong agent tester?
They show instead of explain. Pick any failing test and they open the file, replay it, open the trace and name the
cause in a few minutes.
