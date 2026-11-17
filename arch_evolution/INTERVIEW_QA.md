# Interview questions: how AI assistant architecture evolves

Each answer follows one pattern: **the challenge → what we changed → what improved → the honest limit**.
Say each one out loud in 30 to 45 seconds. The lesson is in [README.md](README.md).

Numbers are from my own repos. "Offline" means a deterministic, keyword-based scripted model used in CI. It
measures plumbing, not a real model.

---

### 1. Walk me through how your assistant's architecture changed over time.

**Challenge.** Version one had a regex router, then a classifier, in front of the model. It worked on phrasings
I knew and failed quietly on the rest.
**What we changed.** One agent loop: the model sees all the typed tools and picks. Code runs tools, verifies the
answer and renders the numbers. Then contracts, bounds, evals and config checks around it.
**What improved.** Wrong routes are no longer silent, and every number in an answer is checked by code.
**Honest limit.** With a weak model, the agent routed worse than the old router: 69.6% against 95.7%.

### 2. Why did you remove the router? Wasn't it working?

**Challenge.** It was working: 95.7% on 46 hard labels. But every new phrasing or tool meant new rules and new
training data, and when it was wrong, the model never got a chance to fix it.
**What we changed.** I took it off the request path and gave the model the full catalog.
**What improved.** One brain instead of two. A new tool is a schema and a description, not a retrain.
**Honest limit.** Routing quality is now model quality. That is why I kept the router as a measured baseline.

### 3. Your new agent scored 69.6% and the old router 95.7%. Isn't that a regression?

**Challenge.** Yes, on that run. The agent was driven by my offline model, which is keyword-only, with no
classifier behind it.
**What we changed.** Nothing to hide the number. I kept it in the eval report next to the router.
**What improved.** I can see exactly what the architecture costs with a weak model, and re-measure with a real one.
**Honest limit.** Architecture alone is not a win. The model and the evals carry it. If a real model does not
beat 95.7%, the router should come back.

### 4. When is a keyword router the right answer?

**Challenge.** Few intents, a cheap model, a tight latency budget.
**What we changed.** In a serving benchmark, rules + classifier routing between a small and large model.
**What improved.** 28% lower cost than always-large, and p50 latency from 4.80 s to 2.62 s.
**Honest limit.** 15% of queries went to a model that was too small. So I gate any router on an eval set.

### 5. How do you stop the model from inventing numbers?

**Challenge.** "Only use tool numbers" was a sentence in the prompt. Nothing enforced it.
**What we changed.** The model never types digits. Each number in a tool result gets a token like `c1.n4`. The
answer uses tokens, a verifier checks them with set lookups, and code renders the real values.
**What improved.** An invented number cannot reach the user. The check is exact, cheap and has a test per rule.
**Honest limit.** It proves where a number came from, not that the answer is relevant or well argued.

### 6. Why not use an LLM to check the answer?

**Challenge.** I wanted a check I could trust in CI.
**What we changed.** A deterministic floor first, and an optional LLM judge on top, advisory only.
**What improved.** The floor never flakes. The judge covers relevance, which the floor cannot.
**Honest limit.** An LLM checker is slow and can fail the same way as the model it checks. My judge refuses to
start if it is the same model as the one under test, and its calibration file is small.

### 7. Why make the final answer a tool call instead of text?

**Challenge.** With prose, the server never knew what kind of answer it got: a fact, a quote, a decline.
**What we changed.** `submit_answer` with typed parts: statement, quote, out of scope, unavailable. Prose counts
as a repair; after two repairs the turn ends as `incomplete`.
**What improved.** Structure for free from the provider's tool calling. Declines are data, not sentences to detect.
**Honest limit.** One more tool for the model to learn, and a weak model burns repairs.

### 8. How do you stop a tool schema change from breaking users?

**Challenge.** A package renamed a field, and it reached users silently.
**What we changed.** A committed snapshot of every tool schema with a hash. CI fails on any diff. At start-up,
each package is admitted by version: pre-release of the pin in dev, exact in staging and prod.
**What improved.** A mismatched package is marked unavailable with a typed reason; the other tools keep working,
and readiness returns 503.
**Honest limit.** Every schema change is now a reviewed diff. A small chore, on purpose.

### 9. How did you choose the step limit for the agent?

**Challenge.** It was "6", picked by feel. Retries inside the adapter were not counted anywhere.
**What we changed.** Every bound is a setting. A per-turn ledger counts model calls, retries, tool calls, tokens
and spend. I measured 38 offline runs and applied a fixed rule: 2x the largest tool-call counts, the largest model-call count plus 2, and 3x the largest token count rounded up to the next 1,000.
**What improved.** Max seen was 3 model calls and about 4,500 tokens, so the defaults are 5 model calls and
14,000 tokens, with a written reason.
**Honest limit.** Those came from a scripted model. A real model explores more, so I re-derive them.

### 10. How do you make LLM evals honest?

**Challenge.** One pass per question hides flakiness, and tuning on the whole set hides over-fitting.
**What we changed.** 3 repeats, gate on pass^3 (all repeats must pass), a flaky list, and a hash-based held-out
split: 18 dev, 12 held out.
**What improved.** A change that only helps the dev questions shows up as a gap on the held-out ones.
**Honest limit.** Offline, the model is deterministic, so pass^3 equals pass@1 (30/30). The machinery only
earns its keep with a live model.

### 11. How do you know an eval number in a document is real?

**Challenge.** A number in a doc could not be traced to the run that made it.
**What we changed.** Every run writes an evidence JSON: commit and dirty flag, model ids, a pinned clock,
hashes of the scenario files and the tool contract, and every result.
**What improved.** "30/30 with both agents" points to a file.
**Honest limit.** The files are not committed; you attach the relevant one to a change.

### 12. What does "fail closed" mean for configuration?

**Challenge.** Any mix of settings started the server. A forgotten variable could switch on a test model in prod.
**What we changed.** One environment setting: dev, staging or prod. Unset means prod. One policy table, checked
before start-up, reports every broken rule at once.
**What improved.** A mistake can only make the server stricter.
**Honest limit.** The laptop setup needs one explicit line, and the table must be kept in step with new settings.

### 13. How do you keep a framework upgrade from breaking your agent?

**Challenge.** The graph agent relies on checkpoints, recursion limits and retries I did not write.
**What we changed.** Four small tests against the real library: resume from a checkpoint, the recursion limit
raises, a retry policy retries.
**What improved.** A dependency bump that changes that behaviour fails CI.
**Honest limit.** The tests tie us to the framework's public API; one keyword changed name across versions.

### 14. If you started a new assistant tomorrow, which stage would you start at?

**Challenge.** Jumping to stage 8 on day one is slow; staying at stage 1 is fragile.
**What we changed.** I start with an agent loop, typed tools and an eval set on day one, plus fail-closed config,
because they are cheap. Verification and contracts come when someone depends on the numbers.
**What improved.** Every later stage has an eval to prove it helped.
**Honest limit.** If the model is small and the intents are few, I would still measure a simple router first.
It might win.
