# Day 12: LLMOps and observability

How you know an AI app is working after you ship it: trace every call, count cost, check every answer,
watch the trends and alert on what matters.

| Video | Short |
|---|---|
| [Day 12, full episode](https://youtu.be/VM3SasF9AAU) | [Your AI app looks healthy. 30% of answers are wrong.](https://youtube.com/shorts/ktFmHL6b3CI) |

| File | What it is |
|---|---|
| [tracing.py](tracing.py) | One trace per request, one span per step, JSON lines; tokens, cost, latency, errors; PII redacted before logging |
| [guards.py](guards.py) | Online checks on every answer: unsupported numbers, unknown funds, refusals, PII leaks; an LLM-judge prompt for sampling |
| [simulate.py](simulate.py) | A week of fake traffic with three hidden incidents (slow provider, bad prompt, topic drift) |
| [monitor.py](monitor.py) | Daily dashboard (p50/p95, error rate, cost, guard pass, thumbs-down, PSI drift) and SLO alerts |
| [INTERVIEW_QA.md](INTERVIEW_QA.md) | 27 interview questions with full explanations, spoken answers and a glossary |
| [LAB.md](LAB.md) | Six hands-on steps: trace, guard, simulate, find the incidents, tune alerts, answer on-call questions |

## Quick start
```bash
python day12_llmops/guards.py
python day12_llmops/monitor.py --selftest
```

## Five lessons
1. Latency, errors and cost can all be green while answers are wrong. Monitor quality, not just uptime.
2. Redact before writing logs. A log store full of customer emails is its own incident.
3. Cheap checks on 100% of traffic, an LLM judge on a sample, humans on the flagged queue.
4. Set alert thresholds from baseline data. Noisy alerts get muted; then real ones are missed.
5. Every trace needs an ID that links the user's question, the tool calls, the prompt version and the answer,
   so one complaint can be replayed end to end.
