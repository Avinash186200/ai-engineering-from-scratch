# Day 12 lab: run an LLM app like production

No API key, no Docker, standard library only. Run every command from the repo root.

## Step 1: trace a request
```bash
python day12_llmops/tracing.py
```
You get three JSON lines: a tool span, an LLM span (tokens, cost, latency) and a failed tool span.
Notice the email in the prompt became `[EMAIL]`: **redact before you log**, never after.
Try: add a phone number (`9876543210`) to the prompt and check it is redacted too.

## Step 2: catch bad answers automatically
```bash
python day12_llmops/guards.py
```
One good answer passes; a made-up number, a made-up fund, a refusal and a PII leak are all caught.
Try: write an answer that says "0.99%" when the data says `0.0099`. Does it pass? (It should: see `pct_ok`.)
Then find an answer that fools the checks. Every cheap check has holes; that is why you also sample
answers for an LLM judge (`judge_prompt`) and for humans.

## Step 3: generate a week of traffic
```bash
python day12_llmops/simulate.py
```
2,100 requests over 7 days are written to `day12_llmops/out/traces.jsonl` (gitignored). Three incidents are hidden in them.
Open the file and look at one line: this is what your log store holds.

## Step 4: find the incidents
```bash
python day12_llmops/monitor.py
```
Read the table before the alerts. Can you see which day the provider got slow, which day a bad prompt shipped,
and which day users changed what they ask?

| Day | What happened | Signal that moved |
|---|---|---|
| 5 | Provider slow, timeouts | p95 latency, error rate (cost per request barely moves) |
| 6 | New prompt invents numbers | guard pass rate, thumbs-down |
| 7 | Users ask about crypto | topic PSI, refusal rate |

Note what did **not** catch day 6: latency, errors and cost all looked healthy. Quality failures are silent;
only quality signals find them.

## Step 5: tune the alerts
Edit `SLO` in `monitor.py`:
- Set `p95_ms` to 2000. Now three of the four normal days (1, 2 and 4) fire false alarms. Too tight an alert gets ignored.
- Set `guard_pass` to 0.5. Now day 6 is missed. Too loose an alert is useless.

Pick thresholds from your baseline days, not from a guess.

## Step 6: answer the on-call questions
Using only `traces.jsonl` (pandas is fine):
1. Which model costs the most per day, and what share of requests goes to it?
2. What would routing *all* definitions to the small model save per month?
3. List the trace IDs of day 6 answers that failed `grounded_numbers`. These are your review queue.

## What real teams use
The same fields go to OpenTelemetry (the standard), and on to Langfuse, LangSmith, Arize Phoenix, Datadog or Grafana.
The tool changes; the signals (latency, errors, cost, quality, drift) do not.
