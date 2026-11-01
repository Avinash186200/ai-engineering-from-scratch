# Design: <prompt>

## 1 Clarify      users | scale | latency | sensitivity | budget
## 2 Requirements functional / non-functional
   Estimates:   queries/day, peak QPS, in flight, tokens, cost
## 3 Boxes      client, API, orchestrator, tools, LLM, state, traces
   Ask: "Where would you like me to go deep?"
## 4 Deep dive  mechanisms + numbers + failure modes
## 5 Security   permissions, PII, secrets, injection, audit
## 6 Operations CI, eval gate, tracing, cost, rollback
## 7 Trade-offs biggest trade-off | v1 | next, and when

---

Worked example (fill-in prompts) for the research assistant chatbot over Indian mutual funds:

1. Clarify: analysts, about 200 questions a day, answer in under 5 s, fund data is internal, budget under Rs 1 a query.
2. Requirements: rank funds, define terms, cite factsheets; never give personal advice.
   Estimates: 200/day is a fraction of 1 QPS on average; size for 10x peaks.
3. Boxes: browser -> FastAPI -> LangGraph agent -> tools over MCP (rank_funds, lookup_definition,
   model_info) + LLM; Postgres checkpointer for state; traces for every step.
4. Deep dive: the rank_funds tool contract (typed inputs, structured output with as_of, top,
   excluded and caveat, explicit errors such as "not a business day"); retries and failover.
5. Security: read-only tools, untrusted text wrapped in <document> tags, secrets from a vault.
6. Operations: golden-set eval gate in CI (90%), tracing, cost per completed task, rollback.
7. Trade-offs: an agent (flexible) vs a router (cheaper, predictable); v1 = agent with a round limit.
