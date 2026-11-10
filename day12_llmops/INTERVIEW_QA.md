# Interview questions: LLMOps and observability

For each question: open **Understand it** and read until it is clear, then say the **Answer** out loud in 30-45 seconds.
Code for every idea is in this folder; the hands-on steps are in [LAB.md](LAB.md).


## LLMOps basics

### 1. What is LLMOps, and how is it different from MLOps?

<details><summary>Understand it</summary>

```text
THE SHORT VERSION
LLMOps is everything you do to keep an LLM application working, affordable and safe AFTER it ships: tracing, cost tracking, quality monitoring, prompt versioning, evals, alerts and incident handling.

WHAT IS THE SAME AS MLOPS
- Version everything (code, data, model, config).
- Automate tests and deployment (CI/CD).
- Monitor in production and alert on problems.
- Detect drift: the world changes, the system degrades.

WHAT IS DIFFERENT
1. You usually do not train the model. You call someone else's model through an API. So the things you version are PROMPTS, tool definitions, retrieval settings and the model name.
2. Outputs are free text, not a number. There is no simple accuracy metric on live traffic. You need proxy signals: groundedness checks, LLM judges, user feedback.
3. Cost is per call and per token, and it can explode (long prompts, agent loops, retries).
4. Failures are often SILENT: the service returns 200 OK in 1 second with a confident wrong answer.
5. The provider can change the model under you, or be slow or down.

ANALOGY
MLOps is running a factory you built. LLMOps is running a restaurant that buys from a supplier: you control recipes (prompts) and quality checks, not the supplier's farm.
```

</details>

**Answer:** LLMOps is the practice of running LLM apps in production: tracing every call, tracking cost and latency, monitoring answer quality, versioning prompts, and alerting. It shares MLOps ideas like versioning, CI/CD and drift monitoring, but differs because we usually don't train the model, outputs are free text with no single accuracy metric, cost is per token, and failures are often silent: a fast, confident, wrong answer. So the core of LLMOps is quality signals, not just uptime.

### 2. Why is monitoring an LLM app harder than monitoring a normal web service?

<details><summary>Understand it</summary>

```text
A NORMAL WEB SERVICE
You watch the four golden signals: latency, traffic, errors, saturation. If those are green, users are usually happy. A wrong answer is a bug you catch with tests before release.

AN LLM APP
The same four signals can all be green while the product is broken:
- The model invents a number (hallucination). Status 200, fast, cheap.
- A prompt change makes answers vague. Nothing errors.
- Retrieval returns the wrong documents. The answer is fluent but wrong.
- Users start asking about topics you never designed for. The bot refuses or guesses.

WHY
1. Non-deterministic: the same input can give different outputs.
2. No ground truth on live traffic: you do not know the right answer for each new question.
3. Many moving parts in one request: retrieval, tools, the model, post-processing. Any one can fail quietly.
4. External dependency: the provider's latency, limits and model versions change.

SO YOU ADD A FIFTH AND SIXTH SIGNAL
- Quality: guard pass rate, judge scores, thumbs-down rate.
- Cost: per request and per day.
Day 12 lab, day 6: latency, errors and cost were healthy while 30% of answers had invented numbers. Only the quality signal caught it.
```

</details>

**Answer:** Because the usual signals (latency, errors, traffic) can all be green while the answers are wrong. LLMs are non-deterministic, there's no ground truth for live questions, and a request has several parts (retrieval, tools, the model) that can each fail quietly. So on top of the golden signals I monitor quality (automatic groundedness checks, a sampled LLM judge, user feedback) and cost per request. In my lab, a bad prompt made 30% of answers invent numbers while latency and errors looked perfect.

### 3. What would you monitor for an LLM application in production? Give me the list.

<details><summary>Understand it</summary>

```text
THE DASHBOARD (memorise these groups)

1. RELIABILITY
- Request volume
- Error rate (by type: provider 5xx, timeouts, rate limits 429, tool errors, parse errors)
- Latency p50 and p95 (and p99 for strict SLAs); time to first token if you stream

2. COST
- Tokens in and out per request
- Cost per request, per user, per feature, per day
- Calls per request (agent loops multiply cost)
- Cache hit rate if you cache

3. QUALITY
- Guard pass rate: answers that pass automatic checks (numbers grounded, no unknown entities, valid JSON)
- Refusal rate
- LLM-judge score on a sample
- User feedback: thumbs down, regenerate clicks, copy rate
- Retrieval: did any retrieved chunk contain the answer? empty-result rate

4. SAFETY
- PII in outputs, prompt-injection attempts detected, blocked tool calls

5. DRIFT
- Input mix: topics, question length, language (PSI)
- Output mix: answer length, tool usage pattern

6. AGENT-SPECIFIC
- Steps per request, tool-call success rate, loops hitting the step limit

TIP: say 'p95 not average'. Averages hide the slow tail that users complain about.
```

</details>

**Answer:** Five groups. Reliability: volume, error rate by type, latency p50 and p95. Cost: tokens and cost per request, per user and per day, and calls per request because agent loops multiply it. Quality: the pass rate of automatic answer checks, refusal rate, an LLM-judge score on a sample, and user feedback like thumbs-down. Safety: PII leaks and injection attempts. Drift: changes in what users ask and in answer length. For agents I add steps per request and tool success rate.

### 4. What is an SLO, and what SLOs would you set for a chatbot?

<details><summary>Understand it</summary>

```text
TERMS
- SLI (indicator): a measured number. Example: p95 latency.
- SLO (objective): the target for it. Example: p95 latency under 3 seconds over 30 days.
- SLA (agreement): a contract with a penalty if you miss. Usually looser than the SLO.
- Error budget: 100% minus the SLO. If availability SLO is 99.5%, you may fail 0.5% of requests. If you burn the budget fast, you stop shipping features and fix reliability.

EXAMPLE SLOs FOR AN LLM CHATBOT
- Availability: 99.5% of requests return a usable answer (including the fallback).
- Latency: p95 time to first token < 2 s; p95 full answer < 8 s.
- Quality: guard pass rate >= 95%; weekly judge-graded groundedness >= 90% on a sample.
- Cost: average cost per conversation under a budget, e.g. $0.05.

HOW TO PICK THE NUMBERS
From a baseline week of real traffic, not from a guess. Set the alert a bit worse than normal so normal noise does not page anyone. In the Day 12 lab, a 2000 ms p95 threshold fired false alarms on three normal days; 3000 ms did not.

INTERVIEW POINT
Include a QUALITY SLO. Most candidates list only latency and uptime.
```

</details>

**Answer:** An SLI is a measured number like p95 latency, the SLO is the target for it, and the SLA is the contract with a penalty. For a chatbot I'd set availability around 99.5% including fallback answers, p95 time to first token under 2 seconds, a quality SLO like 95% of answers passing automatic groundedness checks, and a cost per conversation budget. I set the numbers from a baseline week, not by guessing, so alerts don't fire on normal noise.


## Tracing and logging

### 5. What is a trace and a span? Why do you need tracing in an LLM app?

<details><summary>Understand it</summary>

```text
DEFINITIONS
- Trace: the full story of ONE request, from the user's question to the final answer. It has one trace_id.
- Span: one step inside it, with a start time, duration, status and attributes. Example spans: 'retrieve', 'llm call 1', 'tool rank_funds', 'llm call 2', 'guard checks'.
- Spans nest: the agent span contains the tool spans.

WHAT A SPAN RECORDS IN AN LLM APP
model name, prompt version, input and output tokens, cost, latency, status, error message, tool name and arguments, retrieved document IDs, and (redacted) prompt and answer text.

WHY YOU NEED IT
1. Debugging a complaint: 'the bot told me something wrong yesterday'. With the trace_id you replay exactly what it retrieved, which tool it called, what the model saw.
2. Finding the slow step: is it retrieval, the model or a tool?
3. Cost attribution: which step and which feature spends the tokens.
4. Building eval sets: real failed traces become new test cases.

WITHOUT TRACING
You only have the final answer and a guess. Agents especially are impossible to debug: you cannot see which of 6 steps went wrong.

CODE (Day 12 tracing.py)
with tracer.span('tool', tool='rank_funds') as rec: ...  writes one JSON line with latency and status even if the step raises.
```

</details>

**Answer:** A trace is the whole journey of one request, with one trace ID; a span is one step inside it, like retrieval, an LLM call or a tool call, with timing, status, tokens, cost and the prompt version. I need it because LLM failures are hard to reproduce: when a user says the answer was wrong, the trace shows exactly what was retrieved, which tool ran and what the model saw. It also shows which step is slow and which step spends the money, and failed traces become new eval cases.

### 6. What is OpenTelemetry, and how does it relate to tools like Langfuse or LangSmith?

<details><summary>Understand it</summary>

```text
OPENTELEMETRY (OTel)
An open standard plus libraries for traces, metrics and logs. You instrument your code once with OTel, and you can send the data to any backend (Jaeger, Grafana Tempo, Datadog, Honeycomb, New Relic). It avoids vendor lock-in.
It has 'semantic conventions': agreed names for attributes. There are GenAI conventions for LLM calls: model, input tokens, output tokens, and so on.

LLM-SPECIFIC TOOLS
- Langfuse (open source, self-hostable), LangSmith (from LangChain), Arize Phoenix, Helicone, Weights and Biases Weave.
- They add LLM features on top of tracing: viewing prompts and answers side by side, prompt versioning, datasets from traces, LLM-judge scoring, cost dashboards, human annotation queues.
- Many of them accept OpenTelemetry data, so it is not either/or.

HOW TO CHOOSE
- Already have Datadog or Grafana and need ops signals: OTel into that.
- Need prompt and answer review, eval datasets and annotation: add an LLM tool.
- Data must stay in your cloud (finance, health): self-host Langfuse or Phoenix.

SAFE ANSWER IF YOU HAVEN'T USED ONE
'We used OpenTelemetry. For prompt-level review I would add Langfuse self-hosted because the data must stay in our environment.'
```

</details>

**Answer:** OpenTelemetry is the open standard for traces, metrics and logs: you instrument once and send the data to any backend, so there's no lock-in, and it has semantic conventions for LLM calls like model and token counts. Langfuse, LangSmith or Phoenix sit on top for LLM-specific work: viewing prompts and answers, prompt versions, turning traces into eval datasets, judge scores and annotation. Many accept OpenTelemetry, so I'd use OTel as the base and add a self-hosted LLM tool when data must stay in our cloud.

### 7. What should you log for each LLM call, and what should you never log?

<details><summary>Understand it</summary>

```text
LOG THIS
- trace_id, span_id, user or tenant id (pseudonymous), timestamp
- model name AND version, provider, temperature and other params
- prompt template name and version (not just the rendered text)
- input tokens, output tokens, cost
- latency, time to first token, status, error type, retry count
- tool names, arguments and result size
- retrieved document IDs and scores
- guard results (which checks passed or failed)
- user feedback when it arrives (joined by trace_id)

NEVER LOG (or redact first)
- Passwords, API keys, tokens, connection strings
- Personal data: emails, phone numbers, government IDs, account numbers
- Full documents that are confidential, unless your log store has the same access controls as the source
- Anything your privacy policy or the client contract excludes

RULE: REDACT BEFORE WRITE
If you redact later, the secret already sits in log files, backups and the vendor's servers. The Day 12 tracer runs redact() inside the span before anything is written.

RETENTION
Keep full prompt and answer text for a short time (e.g. 30 days), keep metrics longer. Access to raw logs should be restricted and audited.
```

</details>

**Answer:** For every call I log the trace ID, model and version, prompt template version, parameters, tokens in and out, cost, latency, status and retries, tool calls, retrieved document IDs, guard results, and later the user's feedback joined by trace ID. I never log secrets or personal data: emails, phone numbers, IDs, keys. And I redact before writing, not after, because once a secret is in logs it's in backups and vendor systems too. Raw text gets short retention and restricted access.

### 8. How do you version prompts, and why does it matter?

<details><summary>Understand it</summary>

```text
WHY
A prompt is code. A one-line change ('be more specific') can make the model start inventing numbers. If you don't know which prompt version produced an answer, you can't find the cause of a quality drop or roll back.

HOW
1. Store prompts as files in Git (or in a prompt registry), not as strings scattered in code.
2. Give each a name and version: rank_answer_v7.
3. Log the prompt version on every trace.
4. Change prompts through a pull request, with the eval suite running in CI.
5. Roll out gradually (to 10% of traffic, compare metrics) for big changes.
6. Keep the old version deployable for instant rollback.

WHAT ELSE TO VERSION TOGETHER
Model name, temperature, tool definitions, retrieval settings (chunk size, top_k). A 'config bundle' with one version id is easiest.

DAY 12 LAB LINK
Day 6 incident = a new prompt shipped. With prompt_version on every trace, you'd group the dashboard by version and see that v8 has 70% guard pass while v7 had 100%. Roll back to v7 in one step.
```

</details>

**Answer:** I treat prompts as code: stored in Git with a name and version, changed by pull request with the eval suite running in CI, and the version logged on every trace together with the model, temperature and tool definitions. That matters because a one-line prompt change can quietly break quality. With the version on each trace I can group metrics by version, see exactly when quality dropped, and roll back to the previous version immediately.


## Cost and latency

### 9. How do you calculate and control the cost of an LLM application?

<details><summary>Understand it</summary>

```text
THE FORMULA
cost of one call = input tokens x input price + output tokens x output price
(prices are per million tokens; output is usually 3-5x the input price)
cost of one request = sum over ALL calls in it (an agent may call the model 3-6 times)
monthly cost = cost per request x requests per day x 30

EXAMPLE (illustrative prices: $15 in, $75 out per million)
1,200 tokens in, 120 out -> 1200 x 15/1e6 + 120 x 75/1e6 = 0.018 + 0.009 = $0.027
An agent with 3 calls -> about $0.08. 10,000 requests a day -> about $800 a day.

WHERE COST HIDES
- Long system prompts and chat history resent on every turn
- Retrieval stuffing 20 chunks when 5 would do
- Agent loops and retries
- Using the largest model for easy questions

CONTROLS
1. Measure first: cost per request, per feature, per user.
2. Route: small model for easy tasks (definitions, classification), large model for reasoning. Day 12 sim routes definitions to the small model.
3. Prompt caching (providers discount repeated prefixes) and response caching for repeated questions.
4. Trim context: summarise old history, fewer, better chunks.
5. Limits: max tokens out, max agent steps, per-user daily budget.
6. Batch API for offline jobs (cheaper, slower).
7. Alert on cost per request rising vs baseline.
```

</details>

**Answer:** Cost per call is input tokens times the input price plus output tokens times the output price, summed over every call in the request, because an agent may call the model several times. Then times volume. Cost hides in resent chat history, too many retrieved chunks, agent loops and using a big model for easy questions. I control it by measuring per request and per feature, routing easy tasks to a small model, prompt and response caching, trimming context, hard limits on tokens and agent steps, and alerting when cost per request jumps.

### 10. Why measure p95 latency instead of average latency?

<details><summary>Understand it</summary>

```text
AVERAGE HIDES THE TAIL
Example: 95 requests take 1 s, 5 requests take 20 s.
Average = (95 x 1 + 5 x 20) / 100 = 1.95 s. Looks fine.
p95 = the value that 95% of requests are faster than = about 1 s; p99 = 20 s.
Those 5 users waited 20 seconds. They are the ones who complain and leave.

DEFINITION
pXX = the XXth percentile: sort all latencies, take the value at position XX% of the way up.
p50 = median (typical user). p95 = slow users. p99 = the worst 1%.

WHY LLM LATENCY HAS A BIG TAIL
Long answers, long contexts, agent loops with extra steps, provider queueing at busy hours, retries after timeouts.

FOR STREAMING
Measure time to first token (TTFT) separately. Users perceive speed by when text starts appearing.

DAY 12 LAB
Day 5: p50 went from about 1.1 s to 3.6 s, p95 from about 2 s to 6.5 s. The alert is on p95 > 3000 ms.
```

</details>

**Answer:** Because averages hide the slow tail. If 95 requests take one second and five take twenty, the average is under two seconds and looks fine, but five users waited twenty seconds and they're the ones who leave. p50 tells me the typical experience, p95 and p99 tell me the slow tail. LLM latency has a long tail from long answers, agent loops and provider queues, so I alert on p95, and for streaming I also track time to first token.

### 11. How would you reduce latency in an LLM application?

<details><summary>Understand it</summary>

```text
FIRST: FIND THE SLOW STEP (from traces)
Is it retrieval, the model, a tool, or network? Don't optimise blind.

MODEL SIDE
- Stream tokens: the user sees text in under a second even if the full answer takes 6.
- Smaller or faster model for simple steps (routing, classification, extraction).
- Shorter prompts and fewer chunks: input tokens add latency too.
- Limit output length (max_tokens, 'answer in 3 sentences').
- Prompt caching for long shared prefixes.

APP SIDE
- Run independent tool calls in parallel, not one after another.
- Cache frequent answers and embeddings.
- Precompute heavy things (model scores computed nightly, not per request).
- Async I/O so a server handles many waiting requests.
- Keep connections warm; deploy near the provider region.

AGENT SIDE
- Fewer steps: better tool descriptions so the model picks the right tool first time.
- A hard step limit.

TRADE-OFF
Every speed trick can cost quality (smaller model, fewer chunks). Check the eval suite after each change.
```

</details>

**Answer:** First I use traces to find which step is slow: retrieval, the model or a tool. Then: stream tokens so the user sees text immediately, use a smaller model for simple steps, shorten prompts and retrieved context, cap the output length, cache frequent answers and use prompt caching, run independent tool calls in parallel, and precompute heavy work like model scores in batch. For agents, better tool descriptions mean fewer steps. After each change I rerun evals, because most speed tricks can cost quality.

### 12. What happens when the LLM provider is slow or down? How do you design for it?

<details><summary>Understand it</summary>

```text
FAILURE TYPES
- Rate limit (HTTP 429): too many requests or tokens per minute.
- Server errors (5xx) and timeouts.
- Slow responses (the Day 12 day-5 incident).
- Full outage.
- Silent model change: same name, different behaviour.

DESIGN
1. Timeouts on every call (never wait forever).
2. Retries with exponential backoff and jitter, only for retryable errors (429, 5xx, timeouts), with a max count.
3. Circuit breaker: after N failures, stop calling the provider for a while and fail fast (Day 8).
4. Failover: a second provider or model behind the same adapter interface.
5. Graceful degradation: return something useful without the LLM. Day 8: if every provider is down, /chat returns the raw ranking table.
6. Queue non-urgent work.
7. Pin model versions where the provider allows, and run evals when you change.

MONITOR
Error rate by type and provider, retry counts, circuit-breaker state, failover rate. Alert on them.

INTERVIEW LINE
'A vendor-neutral adapter is what makes failover a config change instead of a rewrite.'
```

</details>

**Answer:** I assume it will happen. Every call has a timeout; retryable errors like 429s, 5xx and timeouts get exponential backoff with jitter and a cap; a circuit breaker stops hammering a failing provider; and a vendor-neutral adapter lets me fail over to a second provider or model by config. If everything is down, the app degrades gracefully, for example returning the raw tool results without the written summary. I pin model versions where possible and monitor error rate by type, retries and failover rate.

### 13. What is caching in LLM apps, and what can go wrong with it?

<details><summary>Understand it</summary>

```text
THREE KINDS
1. Prompt (prefix) caching, done by the provider: a long, repeated prefix (system prompt, tool definitions, a big document) is processed once and reused; later calls are cheaper and faster. You structure prompts so the stable part comes first.
2. Exact response cache, done by you: same normalised question + same context -> return the stored answer. Good for FAQs.
3. Semantic cache: embed the question, and if a stored question is very similar, reuse its answer.

WHAT CAN GO WRONG
- Stale answers: data changed but the cache still serves yesterday's ranking. Put the data date in the cache key, or a short TTL.
- Semantic cache false hits: 'top funds on 2025-06-20' vs 'top funds on 2025-06-19' are very similar text but different answers. Dangerous for numbers and dates.
- Leaking between users: a cached answer built from user A's private documents served to user B. Include the user/tenant and permissions in the key.
- Caching errors or bad answers: never cache failures; don't cache answers that failed guards.

RULE OF THUMB
Provider prompt caching: almost always worth it. Exact cache: safe with good keys. Semantic cache: only for non-numeric, non-personal FAQs.
```

</details>

**Answer:** There are three kinds: provider prompt caching, where a long repeated prefix like the system prompt and tool definitions is processed once and reused; an exact response cache for identical questions; and a semantic cache that reuses answers for similar questions. The risks are stale answers when data changes, semantic false hits where two dates look similar but need different answers, leaking one user's answer to another, and caching failures. So I key caches on data date, user and permissions, never cache failed answers, and use semantic caching only for generic FAQs.


## Quality and hallucination

### 14. How would you detect hallucinations in production?

<details><summary>Understand it</summary>

```text
THE PROBLEM
On live traffic you don't know the right answer, so you can't compute accuracy. You use layers of signals, cheap to expensive.

LAYER 1: CHEAP AUTOMATIC CHECKS ON 100% OF ANSWERS (milliseconds, free)
- Grounded numbers: every number in the answer must appear in the tool results or retrieved text it came from (allowing 0.0099 = 0.99%).
- Known entities: every fund, ticker or product named must exist in the evidence.
- Schema checks: JSON parses, required fields present, values in range.
- Citation check: each cited source ID was actually retrieved.
Day 12 guards.py does the first two and catches a made-up 2.4% and a made-up 'Fund Zeta'.

LAYER 2: LLM-AS-JUDGE ON A SAMPLE (e.g. 2-5%)
A second model gets the question, the evidence and the answer, and returns grounded yes/no plus unsupported claims. Costs money, so sample. Calibrate it against human labels first.

LAYER 3: HUMANS ON THE FLAGGED QUEUE
Answers that failed layer 1 or 2, plus thumbs-down ones, go to a reviewer. Confirmed failures become new eval test cases.

LAYER 4: USER SIGNALS
Thumbs down, regenerate, follow-up 'that's wrong'.

TRACK THE RATE, NOT JUST INDIVIDUAL CASES
Guard pass rate on the dashboard with an alert. A drop from 100% to 70% after a deploy = the prompt broke something.

PREVENTION IS SEPARATE
Grounding the model in tool results/RAG, telling it to say 'I don't know', low temperature for factual tasks.
```

</details>

**Answer:** In layers. First, cheap automatic checks on every answer: every number in the answer must appear in the tool results or retrieved text, every entity it names must exist in the evidence, JSON must validate and citations must point to retrieved sources. Second, an LLM judge on a small sample that compares the answer to the evidence, calibrated against human labels. Third, humans review the flagged and thumbs-down answers, and confirmed failures become eval cases. I put the pass rate on a dashboard with an alert: if it drops after a deploy, the change broke something.

### 15. What is LLM-as-a-judge? What are its problems?

<details><summary>Understand it</summary>

```text
WHAT
Use an LLM to grade another LLM's output against a rubric: groundedness, relevance, correctness vs a reference answer, tone, safety. Output a score or pass/fail plus a reason, ideally as JSON.

WHY
Humans are slow and expensive; exact-match metrics don't work for free text. A judge scales.

PROBLEMS (know at least four)
1. Bias toward longer or more confident answers.
2. Position bias in pairwise comparisons (prefers the first or second option): swap order and average.
3. Self-preference: a model rates its own family's outputs higher. Use a different model as judge where possible.
4. It can hallucinate too: wrong judgments.
5. Cost and latency: it's another LLM call, so sample.
6. Drift: if the judge model changes, scores shift without your system changing.

HOW TO MAKE IT TRUSTWORTHY
- Narrow, concrete rubric ('is every number supported by the evidence?' not 'is this good?').
- Give it the evidence; ask for the unsupported claims, not just a score.
- Calibrate: 100-200 human-labelled examples, measure agreement (accuracy or Cohen's kappa) before trusting it.
- Pin the judge model version; re-calibrate when it changes.
- Use for trends and triage, not as the only gate on a single answer.
```

</details>

**Answer:** LLM-as-a-judge means using a model to grade outputs against a rubric, like whether every claim is supported by the evidence, returning a structured verdict. It scales where humans can't. Its problems are length and confidence bias, position bias in pairwise comparisons, self-preference, its own hallucinations, cost, and drift if the judge model changes. So I keep the rubric narrow, give it the evidence, ask for the unsupported claims, calibrate it against a couple of hundred human labels before trusting it, pin its version, and use it on a sample for trends rather than as the only gate.

### 16. Offline evals vs online monitoring: what's the difference and why do you need both?

<details><summary>Understand it</summary>

```text
OFFLINE EVALS (before release)
- A fixed golden set of questions with expected answers or rubrics.
- Run in CI on every change to prompts, models, retrieval or code.
- Blocks the merge if the pass rate drops (Day 6 eval gate: fail if < 90%).
- Catches regressions on KNOWN cases.

ONLINE MONITORING (after release)
- Real traffic, no answer key.
- Proxy signals: guards, sampled judge, user feedback, drift.
- Catches problems on UNKNOWN cases: new kinds of questions, provider changes, data changes.

WHY BOTH
Offline can't cover what users will actually ask. Online can't stop a bad change before users see it.

THE LOOP THAT CONNECTS THEM
production failure -> trace -> human confirms -> add to golden set -> the next change is tested against it.
Over time the golden set looks more and more like real traffic.

ADD: SHADOW AND CANARY
- Shadow: run the new prompt on live traffic in the background, compare, don't show users.
- Canary: show the new version to 5-10% of users, compare live metrics, then roll out.
```

</details>

**Answer:** Offline evals run a fixed golden set in CI before release and block a change if the pass rate drops; they catch regressions on known cases. Online monitoring watches real traffic with proxy signals like groundedness checks, a sampled judge and user feedback; it catches what the golden set never covered: new question types, provider or data changes. I need both, and I connect them: a confirmed production failure gets added to the golden set, so the next change is tested against it. For risky changes I also use shadow runs or a canary.

### 17. How do you collect and use user feedback?

<details><summary>Understand it</summary>

```text
COLLECT
- Explicit: thumbs up/down, a reason dropdown ('wrong', 'incomplete', 'off-topic'), free text.
- Implicit: regenerate clicks, copying the answer (good sign), rephrasing the same question (bad sign), abandoning the session, escalating to a human.
- Always join feedback to the trace_id so you can see the full context.

LIMITS
- Few users click (often 1-5%), and unhappy users click more: biased sample.
- Thumbs-up doesn't mean correct; users can't always tell a confident wrong answer.
So feedback is one signal, not the truth.

USE
1. Dashboard: thumbs-down rate per day, per feature, per prompt version.
2. Triage queue: thumbs-down traces reviewed by a person weekly.
3. Eval set: confirmed bad answers become test cases with the right answer.
4. Prioritise: cluster the complaints (topic, failure type) to decide what to fix.
5. In Day 12 sim, thumbs-down jumps from about 8% to 23-27% on incident days.

FINANCE CONTEXT
For analysts, expert review of a small weekly sample is worth more than many casual clicks.
```

</details>

**Answer:** Explicitly with thumbs up or down and a reason, and implicitly from regenerate clicks, rephrasing, copying or abandoning, always joined to the trace ID. Feedback is biased, since few users click and unhappy ones click more, and users can't always spot a confident wrong answer, so it's one signal, not truth. I track the thumbs-down rate per prompt version, review the thumbs-down traces weekly, turn confirmed failures into eval cases, and cluster complaints to decide what to fix first.


## Drift and change

### 18. What is drift in an LLM application? How do you detect it?

<details><summary>Understand it</summary>

```text
TYPES OF DRIFT
1. Input drift: users ask different things (new topics, longer questions, another language). Day 12 day 7: crypto questions appear.
2. Data drift: the documents or database the app relies on change (new funds, stale index, a broken pipeline feeding old data).
3. Model drift: the provider updates the model, or you switch models; behaviour changes.
4. Output drift: answer length, refusal rate, tool usage change.

DETECTING INPUT DRIFT
- Classify each question into a topic (rules, embeddings + clustering, or a small model).
- Compare today's topic mix to a baseline with PSI (Population Stability Index):
  PSI = sum over topics of (now% - base%) x ln(now% / base%)
  < 0.1 stable, 0.1-0.2 watch, > 0.2 real shift.
- Also track embedding distance between today's questions and the baseline (centroid shift), question length, language.
Day 12 lab: PSI about 2.9 on day 7 vs under 0.03 on normal days.

DETECTING THE OTHERS
- Data: freshness checks ('latest data date' metric), row counts, retrieval empty-result rate.
- Model: log the model version; rerun the golden set on a schedule (weekly), not only on code changes.
- Output: refusal rate, answer length distribution, tools per request.

WHAT TO DO
New topic you should cover: add a tool or documents and eval cases. Out of scope: a clear, polite refusal (and measure it).
```

</details>

**Answer:** Drift means the conditions change: users ask different things, the underlying data changes or goes stale, the provider changes the model, or outputs shift in length, refusals or tool use. For input drift I classify questions into topics and compare today's mix to a baseline with PSI, where above 0.2 means a real shift, plus embedding distance and length. For data drift I monitor freshness and row counts; for model drift I log the model version and rerun the golden set weekly; for output drift I watch refusal rate and answer length. In my lab, PSI went from under 0.03 to about 2.9 when crypto questions appeared.

### 19. Your provider silently updates the model. How would you notice, and what would you do?

<details><summary>Understand it</summary>

```text
HOW YOU NOTICE
- The model version string in responses changes (log it on every trace).
- Scheduled golden-set run (e.g. nightly or weekly) shows a different pass rate.
- Online metrics shift: answer length, refusal rate, guard pass rate, JSON parse errors, tool-call pattern.
- User feedback moves.

PREVENT AND PREPARE
- Pin a dated model version when the provider offers it, not a floating alias like 'latest'.
- Keep your eval suite runnable on demand with one command.
- Use a vendor-neutral adapter so you can switch model or provider by config.
- Read provider deprecation notices; plan migrations.

WHAT TO DO WHEN IT HAPPENS
1. Confirm with the golden set: old vs new version side by side.
2. If worse: pin back to the old version if still available, or fail over.
3. Adjust prompts for the new model, re-run evals, roll out with a canary.
4. Record it: date, version, effect, fix.

INTERVIEW LINE
'Treat a model change exactly like a code change: it goes through evals before users get it.'
```

</details>

**Answer:** I log the model version on every trace and run the golden set on a schedule, so a silent change shows up as a version string change, a shift in eval pass rate, or online shifts in answer length, refusals, parse errors or guard pass rate. To prevent it I pin dated model versions instead of floating aliases. If it happens, I compare old and new on the golden set, pin back or fail over if the new one is worse, adapt the prompt, re-run evals and roll out with a canary. A model change is treated like a code change.


## Alerts and incidents

### 20. How do you design alerts so they're useful and not noisy?

<details><summary>Understand it</summary>

```text
PRINCIPLES
1. Alert on symptoms users feel (p95 latency, error rate, quality drop), not every internal metric.
2. Every alert must have an owner and a clear action. If nobody would do anything, it's a dashboard metric, not an alert.
3. Thresholds from a baseline, not a guess. Day 12 lab: 2000 ms fired on 3 normal days; 3000 ms fired only on the real incident.
4. Use windows and minimum counts: 'p95 > 3 s for 10 minutes with at least 100 requests', so one slow request doesn't page.
5. Severity levels: page (wake someone up) vs ticket (look tomorrow).
6. Compare to baseline for things without a fixed target (cost per request > 1.5x the last 7 days; PSI > 0.2).
7. Review alerts monthly: delete the ones that never led to action.

ALERT FATIGUE
Too many false alarms -> people mute the channel -> the real one is missed. A noisy alert is worse than none.

GOOD LLM ALERTS
- Error rate > 2% for 10 min (page)
- p95 latency > SLO for 15 min (page)
- Guard pass rate < 95% over 1 hour (page if sudden)
- Cost per request > 1.5x baseline (ticket)
- Topic PSI > 0.2 over a day (ticket)
- Data freshness: latest data older than 1 business day (page for finance)
```

</details>

**Answer:** I alert only on things users feel and someone will act on: error rate, p95 latency against the SLO, a drop in the answer-quality pass rate, cost per request against baseline, drift, and data freshness. Thresholds come from a baseline week, with time windows and minimum request counts so one slow request doesn't page anyone, and two severities, page versus ticket. I review alerts monthly and delete those that never led to action, because a noisy alert gets muted and then the real one is missed.

### 21. Walk me through how you'd handle a production incident in an LLM app.

<details><summary>Understand it</summary>

```text
THE STEPS
1. Detect: alert fires or a user reports.
2. Triage: how bad, how many users, since when? Declare severity. One person leads, one communicates.
3. Mitigate FIRST, diagnose second: stop the bleeding.
   - Roll back the last deploy or prompt version.
   - Fail over to another provider/model.
   - Turn on the degraded mode (raw tool results, no LLM summary).
   - Disable the broken feature with a flag.
4. Communicate: a short status to users/stakeholders, then updates on a schedule.
5. Diagnose: traces of failing requests, group by prompt version, model version, provider, topic, data date.
6. Fix properly and verify with the golden set and live metrics.
7. Postmortem (blameless): timeline, root cause, why detection took as long as it did, actions (new alert, new eval case, new guard).

EXAMPLE (Day 12 day 6)
Alert: guard pass rate 71%. Triage: started at the 10:00 deploy, 30% of ranking answers. Mitigate: roll back prompt v8 to v7, pass rate back to 100%. Diagnose: v8 said 'be confident and specific', model began projecting returns. Fix: remove the line, add 10 eval cases that check numbers are grounded. Postmortem action: prompt changes now require the eval gate.
```

</details>

**Answer:** Detect, triage, mitigate, then diagnose. I size the impact and set a severity, then stop the bleeding first: roll back the last deploy or prompt version, fail over, switch to a degraded mode, or turn off the feature with a flag. Then I communicate status, and diagnose from traces grouped by prompt version, model, provider and topic. I fix it, verify with the golden set and live metrics, and write a blameless postmortem whose actions are concrete: a new alert, new eval cases, a new guard. For example, a prompt change that made answers invent numbers: roll back first, then fix and add eval cases.

### 22. What is a postmortem, and what makes a good one?

<details><summary>Understand it</summary>

```text
WHAT
A written review after an incident: what happened, why, and what changes so it doesn't happen again.

BLAMELESS
Focus on systems and process, not people. 'The deploy pipeline allowed a prompt change without evals', not 'X broke prod'. People only share the truth if they won't be punished.

STRUCTURE
1. Summary: one paragraph, impact in numbers (how many users, how long, what was wrong).
2. Timeline: when it started, detected, mitigated, resolved (with times).
3. Root cause: ask 'why' repeatedly (5 whys) until you reach something you can change.
4. What went well, what went badly, where we got lucky.
5. Action items: each with an owner and a date. Concrete: 'add alert on X', 'add 10 eval cases', 'require eval gate for prompt PRs'.

GOOD vs BAD ACTION ITEMS
Bad: 'be more careful'. Good: 'CI blocks prompt PRs if grounded-number pass rate < 98%'.

KEY METRICS
Time to detect, time to mitigate. Shortening time to detect is usually the biggest win: better monitoring.
```

</details>

**Answer:** A postmortem is a blameless written review after an incident: a summary with the impact in numbers, a timeline from start to detection to mitigation, the root cause found by asking why until we reach something changeable, what went well and badly, and concrete action items with owners, like a new alert or an eval gate, never 'be more careful'. I pay attention to time to detect, because better monitoring usually shrinks it the most.


## Design and scenarios

### 23. Design the observability for an AI assistant used by analysts at a financial firm.

<details><summary>Understand it</summary>

```text
STRUCTURE YOUR ANSWER (5 parts)

1. INSTRUMENT
OpenTelemetry tracing on every service: one trace per question; spans for retrieval, each LLM call, each tool call, guards. Attributes: model and version, prompt version, tokens, cost, latency, tool args, doc IDs, data as-of date. Redact PII and client identifiers before export.

2. STORE
Traces and metrics in the firm's own cloud (self-hosted Langfuse or Phoenix plus Grafana/Prometheus), because the data is confidential. Raw text retention 30 days with restricted, audited access; metrics 13 months.

3. CHECK EVERY ANSWER
Grounded numbers against tool results; known securities only; schema validation; mandatory caveat present ('research signal, not advice'). Fail -> show a safe fallback and flag.
Sampled LLM judge (5%), weekly expert review of flagged answers.

4. DASHBOARD + ALERTS
Reliability (errors, p95), cost per analyst per day, quality (guard pass, judge, thumbs-down), drift (topics), DATA FRESHNESS (latest market data date — critical in finance), tool success rate. Alerts with owners; page on freshness and quality drops.

5. CLOSE THE LOOP
Failures -> golden set; scheduled eval runs; prompt and model changes go through CI evals and canary; monthly review with users.

FINANCE EXTRAS
Audit trail: which data and model version produced each number (regulators and clients may ask). Point-in-time correctness: show the as-of date in every answer.
```

</details>

**Answer:** I'd do five things. Instrument every service with OpenTelemetry, with one trace per question and spans for retrieval, LLM calls, tools and guards, recording model and prompt versions, tokens, cost and the data as-of date, redacting client data before export. Store it inside the firm's cloud, for example self-hosted Langfuse plus Grafana, with short retention and audited access for raw text. Check every answer: numbers grounded in tool output, known securities only, and the required caveat, with a sampled judge and weekly expert review. Dashboard and alerts on reliability, cost, quality, drift and especially data freshness. Then close the loop: failures go into the golden set, and every change goes through CI evals and a canary. In finance I'd add an audit trail of which data and model version produced each number.

### 24. Your LLM costs doubled this month. How do you investigate?

<details><summary>Understand it</summary>

```text
STEP BY STEP
1. Is it volume or unit cost? cost = requests x cost per request. Did requests double, or did cost per request?
2. If volume: which users, features, tenants? A new integration, a bot or script hammering the API, a retry loop?
3. If unit cost: break cost per request into parts from traces:
   - tokens in per call (did prompts or context grow? chat history not trimmed? more retrieved chunks?)
   - tokens out (answers longer? max_tokens raised?)
   - calls per request (agent taking more steps? retries up after provider errors?)
   - model mix (did routing send more traffic to the large model? did someone change the default?)
4. Find the change point: plot daily cost per request, line it up with deploys and prompt versions.
5. Fix: roll back or adjust the change, trim context, fix routing, cap steps, add caching, set per-user budgets.
6. Prevent: alert on cost per request > 1.5x baseline, cost per feature dashboard, budgets in the provider console.

COMMON REAL CAUSES
History resent in full on every turn; a retry storm during a provider incident; agent loops; a prompt edit that added a 3,000-token example.
```

</details>

**Answer:** First, split it: did volume double or cost per request? If volume, find which users or features, often a new integration, a script or a retry loop. If cost per request, use traces to split it into input tokens, output tokens, calls per request and model mix, then line up the change point with deploys and prompt versions. Common causes are full chat history resent each turn, a retry storm, agent loops, or routing sending everything to the big model. Then fix it, and add an alert on cost per request against baseline and per-feature budgets.

### 25. The bot gives a wrong answer to an important client. Walk me through what you do.

<details><summary>Understand it</summary>

```text
IMMEDIATELY
1. Get the trace (trace_id from the session, or search by user and time).
2. Correct the record with the client quickly and honestly: what was wrong, the right number, the fix in progress.

DIAGNOSE WITH THE TRACE: WHERE DID IT GO WRONG?
- Input: did we misunderstand the question (wrong date, wrong security)?
- Retrieval/tools: did the tool return the right data? Was the data stale or missing (data freshness)?
- Generation: did the model misread correct data or invent something (grounded-number check would show)?
- Post-processing: formatting, unit conversion (0.0099 vs 0.99%)?

CHECK THE SCOPE
Is it a one-off or a pattern? Search traces for the same failure type in the last N days. Check guard pass rate and recent deploys.

FIX AND PREVENT
- Fix the root cause (data pipeline, prompt, tool, guard).
- Add the case and variants to the golden set.
- Add or tighten a guard so this class is caught before a user sees it.
- If it's a stale-data problem, add a freshness check and show the as-of date in answers.

COMMUNICATION RULE
Never present a research model as certain. The answer should have carried a caveat and an as-of date.
```

</details>

**Answer:** I pull the trace for that conversation and quickly tell the client what was wrong and the correct figure. Then I use the trace to find where it broke: misread question, wrong or stale data from the tool, the model inventing or misreading a number, or a formatting or unit error. I check whether it's a pattern by searching traces for the same failure and looking at recent deploys. Then I fix the root cause, add the case to the golden set, and add a guard so that class of error is caught before users see it, like a grounded-number check or a data freshness check with the as-of date shown.

### 26. Which LLMOps tools have you used, and how would you choose between them?

<details><summary>Understand it</summary>

```text
HONEST ANSWER SHAPE
Say what you used, then how you'd choose. Never claim a tool you haven't used.

THE LANDSCAPE
- Standard: OpenTelemetry (traces, metrics, logs).
- Backends: Grafana + Prometheus + Tempo/Loki, Jaeger, Datadog, Honeycomb, New Relic.
- LLM-specific: Langfuse (open source, self-host), LangSmith (LangChain), Arize Phoenix (open source), Helicone (proxy), W&B Weave, Braintrust.
- Evals: promptfoo, DeepEval, Ragas (RAG metrics), OpenAI/Anthropic eval tooling, your own harness.
- Guardrails: Guardrails AI, NeMo Guardrails, or your own checks.

CHOOSING CRITERIA
1. Data residency: can prompts leave your cloud? If not, self-hosted.
2. What you already run: if Datadog is the company standard, send OTel there first.
3. Needs: just ops metrics, or prompt review, datasets, annotation, judges?
4. Framework coupling: LangSmith is easiest with LangChain/LangGraph; Langfuse and Phoenix are framework-neutral.
5. Cost at your volume, and open standards (OTel) to avoid lock-in.

SCRIPT
'We used OpenTelemetry across the services. For prompt-level work I'd add Langfuse self-hosted, because client data had to stay in our environment, and it accepts OTel so we wouldn't re-instrument.'
```

</details>

**Answer:** We instrumented with OpenTelemetry, which is the standard. Beyond that I choose by a few criteria: data residency first, since client prompts often can't leave our cloud, which points to self-hosted Langfuse or Phoenix; what the company already runs, so OTel into Datadog or Grafana; whether we need prompt review, datasets and judges or just ops metrics; framework coupling, as LangSmith fits LangChain best; and cost and lock-in. For evals I'd use our own harness or promptfoo, and Ragas for RAG metrics.

### 27. How do you safely roll out a new prompt or model?

<details><summary>Understand it</summary>

```text
THE PIPELINE
1. Change in a branch; pull request.
2. CI runs the offline eval suite (golden set + safety cases + format checks). Merge blocked below threshold.
3. Compare to the current version on the same set: accuracy, groundedness, cost per request, latency. A better score with 2x the cost may not be worth it.
4. Shadow (optional): run the new version on live traffic in the background; compare outputs and metrics without showing users.
5. Canary: 5-10% of users get the new version; watch guard pass rate, thumbs-down, latency, cost, errors for a set period.
6. Full rollout if metrics hold; otherwise roll back instantly (old version still deployed, switched by config/flag).
7. Log the version on every trace so the dashboard can be split by version.

KEY IDEA
Prompts and models are config; config changes are deploys; deploys go through tests and gradual rollout.
```

</details>

**Answer:** Like any deploy. The change goes through a pull request where CI runs the eval suite and blocks the merge below threshold, comparing quality, cost and latency against the current version. For bigger changes I shadow it on live traffic, then canary it to 5 to 10 percent of users and watch answer quality, feedback, latency, cost and errors. If it holds, full rollout; if not, an instant rollback by config, because the old version stays deployed. The version is on every trace so I can compare them on the dashboard.


## Glossary

| Term | Meaning |
|---|---|
| Trace | The whole journey of one request, with one trace_id. |
| Span | One timed step inside a trace: retrieval, LLM call, tool call, guard. |
| OpenTelemetry (OTel) | Open standard and libraries for traces, metrics and logs; vendor-neutral. |
| p50 / p95 / p99 | Latency percentiles: typical user / slow users / worst 1%. |
| TTFT | Time to first token: how fast streaming text starts appearing. |
| SLI / SLO / SLA | Measured number / its target / contract with a penalty. |
| Error budget | 100% minus the SLO: how much failure you can afford before stopping feature work. |
| Guard (online check) | Automatic check on every answer before the user sees it. |
| Grounded | Every claim in the answer is supported by the evidence (tool results, retrieved text). |
| LLM-as-judge | A model grading another model's output against a rubric; calibrate against humans. |
| Golden set | Fixed questions with expected answers or rubrics, run in CI. |
| Shadow / canary | Run new version silently on live traffic / show it to a small % of users first. |
| Drift | Inputs, data, model or outputs change over time. |
| PSI | Population Stability Index: sum((now-base) x ln(now/base)); > 0.2 = real shift. |
| Prompt versioning | Prompts stored in Git with a version logged on every trace. |
| Prompt caching | Provider reuses a repeated prompt prefix: cheaper and faster. |
| Circuit breaker | Stop calling a failing dependency for a while; fail fast. |
| Graceful degradation | Return something useful (e.g. raw tool results) when the LLM is unavailable. |
| Redaction | Remove PII and secrets before writing logs. |
| Postmortem | Blameless written review: impact, timeline, root cause, action items with owners. |
| Alert fatigue | Too many false alarms make people ignore alerts, so real ones are missed. |
| Data freshness | How old the latest data is; critical in finance. |
