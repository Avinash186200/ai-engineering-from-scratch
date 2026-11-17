# System design for AI and ML products

A method for the 45-minute design round, plus eight worked designs to practise on: four AI and four ML. The short
template is in [`day09_design/design_template.md`](../day09_design/design_template.md); this folder goes deeper.

| File | What |
|---|---|
| `README.md` | How the round is scored, the 7-step method, estimate rules of thumb |
| [`star_template.md`](star_template.md) | Behavioural answers: STAR shape, a story bank to fill, standard questions |
| [`01_document_qa.md`](01_document_qa.md) | Document Q&A for a 10,000-person company (RAG with permissions) |
| [`02_forecast_copilot.md`](02_forecast_copilot.md) | A copilot over live demand-forecast models (tools, grounding, parity) |
| [`03_multi_tenant_platform.md`](03_multi_tenant_platform.md) | An agent platform that many separate organisations share |
| [`04_support_triage_agent.md`](04_support_triage_agent.md) | A support-ticket agent that can take actions (permissions, human approval) |
| [`05_churn_prediction_with_retraining.md`](05_churn_prediction_with_retraining.md) | Subscription churn: late labels, calibration, retraining policy, promotion gates |
| [`06_fraud_detection_realtime.md`](06_fraud_detection_realtime.md) | Card fraud scoring under 100 ms: feature parity, extreme imbalance, cost-based thresholds |
| [`07_demand_forecasting.md`](07_demand_forecasting.md) | Demand per item and store: hierarchy, intermittent demand, walk-forward backtests |
| [`08_ranking_recommendations.md`](08_ranking_recommendations.md) | Recommendations: retrieval and ranking, offline metrics against A/B tests, position bias |

## What the interviewer scores

1. **Scoping**: do you ask before you draw? Users, scale, latency, data sensitivity, budget.
2. **Structure**: a clear high-level picture before details.
3. **Depth**: one hard part explained with mechanisms and numbers, not buzzwords.
4. **Trade-offs**: every choice comes with the alternative and why you did not pick it.
5. **Operations**: how you test, deploy, observe and roll back. This is where AI designs usually fall short.

Signals of seniority: you state assumptions out loud, you size the system with quick numbers, you name failure
modes before being asked, and you cut a v1.

## The 7 steps (about 30 minutes of talking)

| Step | Time | Say |
|---|---|---|
| 1 Clarify | 2 min | Who uses it, how many, how fast must it answer, how sensitive is the data, what budget |
| 2 Requirements | 2-4 min | Functional (what it answers or does) and non-functional (latency, accuracy, audit, cost); quick estimates |
| 3 Boxes | 5 min | Front end, API, orchestrator or agent, tools and retrieval, LLM, state store, tracing. Then ask where to go deep |
| 4 Deep dive | 10 min | The hardest part: retrieval, tool contracts, grounding, memory, or the eval loop |
| 5 Data and security | 3 min | Access control, PII, secrets, prompt injection, audit log |
| 6 Operations | 3 min | CI with an eval gate, tracing, cost controls, canary and rollback |
| 7 Trade-offs | 3 min | What v1 leaves out, what comes next, and what would trigger it |

In the ML designs (05-08) the deep dive is usually the label and its delay, leakage, the metric and the threshold,
or retraining and monitoring.

Say the trade-off every time: "Retrieval rather than fine-tuning, because the documents change weekly and users
need citations."

## Estimates: rules of thumb

- Requests per second: daily requests / 86,400, then multiply by 5-10 for the peak hour.
- Requests in flight: peak RPS x average latency in seconds (Little's law). 20 RPS x 4 s = 80 concurrent.
- Tokens per day: requests x (input + output tokens). Cost: tokens x price per token, output priced higher.
- Embedding storage: chunks x dimensions x 4 bytes. 2 M chunks x 1,024 dims x 4 B = about 8 GB, before index overhead.
- Rate limits: compare peak tokens per minute with the provider limit early; it is often the first wall.

## Common probes, and a one-line answer

- "The LLM provider is down." Retries with backoff, then failover to a second provider, then a degraded answer
  (raw tool output, or "try again"), behind a circuit breaker.
- "Cost doubled overnight." Cost per request by route and user from traces; look for loops, longer prompts,
  cache misses or a model change; add per-user budgets.
- "Answers got worse after a release." Compare golden-set scores between versions, roll back, add the failing case.
- "10x the users." Stateless API replicas, state in the database, cache common answers, queue long jobs, raise
  provider limits.
