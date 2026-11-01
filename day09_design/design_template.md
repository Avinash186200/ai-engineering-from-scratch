# AI system design template

Use this in a system design interview or before building. Fill each section in 2-5 lines.
Worked example in brackets: a research assistant chatbot over Indian mutual fund data.

## 1. Problem and users
Who uses it, for what decision, how often. [Analysts ask about funds ~200 times a day.]

## 2. Requirements
- Functional: what it must answer. [Rank funds, define terms, cite factsheets.]
- Non-functional: latency target, availability, cost per query, privacy. [p95 < 5 s, < 1 rupee/query.]
- Out of scope: what it must refuse. [Personal investment advice.]

## 3. Data
Sources, freshness, size, who owns them, point-in-time correctness. [Daily NAV panel, factsheets.]

## 4. Architecture
Draw the boxes: client -> API -> agent (LLM + tools) -> model / retriever / database.
Say which parts are deterministic code and which are LLM calls, and why.

## 5. Model choices
LLM (size, provider, fallback), embedder, ranker. Prompting vs RAG vs fine-tuning, and why.

## 6. Tools and retrieval
Tool list with input schemas. Chunking, hybrid search, top-k, reranking.

## 7. Evaluation
Golden set (size, who labels it), metrics (tool accuracy, hit@k, faithfulness), CI gate threshold.

## 8. Safety and security
Prompt injection defences, least-privilege tools, PII handling, secrets management, audit logs.

## 9. Reliability and cost
Retries with backoff, failover provider, circuit breaker, timeouts, caching, token budgets.

## 10. Rollout and monitoring
Shadow mode, canary, dashboards (latency, errors, cost, eval drift), rollback plan.

## 11. Risks and open questions
Top three things that could go wrong and what you would test first.
