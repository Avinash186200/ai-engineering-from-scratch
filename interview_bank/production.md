# Production

Code to back these answers: `day08_production/`, `day12_llmops/`, `day13_cloud/`.
Checklist: [`day08_production/ROLLOUT_CHECKLIST.md`](../day08_production/ROLLOUT_CHECKLIST.md).

### 1. How is an LLM service deployed?
Each service in a Docker image tagged by commit; CI builds and tests it; the same image goes to staging, then
production behind HTTPS. State lives in a managed database, secrets in a secrets manager. Release with a canary and
keep the previous image for rollback.

### 2. Why put a vendor-agnostic layer in front of the LLM?
One adapter owns provider calls, so switching or adding a provider is a config change, and retries, timeouts,
failover, logging and cost tracking live in one place. A lint rule can block direct imports of provider SDKs.

### 3. The LLM API goes down mid-request. What happens?
Retry transient errors with backoff and a time budget, fail over to a second provider, and if all fail, return a
degraded answer (for example the raw tool result) or a clear error. A circuit breaker stops hammering a dead provider.

### 4. Your LLM bill doubled. What do you do?
Break cost down by route, model, user and prompt version from traces. Typical causes: an agent loop, a longer
prompt, lost cache hits, a model change, or one heavy user. Fix the cause and add a budget alert.

### 5. How do you monitor it?
Service signals (error rate, latency percentiles, traffic) plus LLM signals: tokens and cost per request, tool
failure rate, refusal rate, groundedness checks on a sample, and user feedback. Alert on changes, not only on outages.

### 6. How do you handle data freshness?
Every tool result and document carries an as-of date or version. Pipelines check that data arrived and is plausible
before the service uses it, and answers state the as-of date.

### 7. How is data security handled?
Authenticated users, least-privilege tools, secrets in a manager, PII kept out of logs and prompts where possible,
encryption in transit and at rest, and an audit log of tool calls.

### 8. How do you version prompts and models?
Prompts live in the repo with the code and go through review and the eval gate. The model name is pinned in config.
Traces record the prompt version and model for every call, so you can compare and roll back.

### 9. How do you handle rate limits?
Know your limits in tokens and requests per minute, queue and smooth bursts, back off on 429s, spread across
deployments or providers, and set per-user limits so one user cannot use up everyone's share.

### 10. How do you serve the same model to chat, spreadsheets and notebooks?
One tool or model service with a versioned API. The agent calls it as a tool; spreadsheets and notebooks call the
REST endpoint. A contract test keeps the outputs identical (see `day17_product/`).

### 11. What does CI check?
Lint and types, unit tests, property tests, API contract tests, a secrets scan, and the eval gate on the golden set.
Build the image once and deploy that exact image.

### 12. How would you scale to many more users?
Stateless API replicas behind a load balancer, state in the database, caching, background queues for long jobs,
higher provider limits or several providers, and per-tenant quotas.

### 13. Tell me about an incident.
Use four beats: what changed, what broke and who noticed, how you rolled back and found the cause, and the rule or
test you added so it cannot recur. Keep it blame-free.

### 14. How do you know the deployed version is the one you think?
Check the running image digest or commit through a version endpoint, not just the tag, and log it at start-up.
