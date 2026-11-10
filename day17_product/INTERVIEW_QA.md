# Interview questions: Models as a product: APIs, gateways, Excel and versioning

For each question: open **Understand it** and read until it is clear, then say the **Answer** out loud in 30-45 seconds.
Code for the ideas is in this folder; the hands-on steps are in [LAB.md](LAB.md).


## Serving models

### 1. How would you expose an ML model so an AI agent, Excel users and notebooks can all use it?

<details><summary>Understand it</summary>

```text
ONE IMPLEMENTATION, MANY CHANNELS
1. The model logic lives in one place (a library/function or one service). Nothing is re-implemented per channel, so answers never disagree.
2. Channels in front of it:
   - Agent: an MCP server (or function-calling tool definitions) with typed parameters and clear descriptions.
   - Excel/BI: a REST API (JSON for Power Query, CSV for simple 'From Web'), or an add-in that calls the API.
   - Notebooks/scripts: the REST API through a small client library (auth, retries, DataFrames).
   - Services: REST with OpenAPI docs; gRPC if latency/volume demand it.
3. An MCP-to-REST gateway (e.g. mcpo) can turn MCP tools into REST endpoints with OpenAPI automatically, so tools are written once.

COMMON CONCERNS (one layer for all channels)
Auth (keys/tokens per client), rate limits, logging/tracing, versioning, typed errors, as-of dates and model versions in every response, caching of expensive results.

WHY
Analysts live in spreadsheets; agents need tools; quants need notebooks. Meeting users where they work is what makes a model used.
```

</details>

**Answer:** I keep one implementation of the model and put channels in front of it: an MCP server for the agent, a REST API with OpenAPI for services and spreadsheets, JSON for Power Query or CSV for simple imports, and a small Python client for notebooks. A gateway like mcpo can expose MCP tools as REST automatically, so tools are written once. Auth per client, rate limits, tracing, versioning, typed errors and the model version and as-of date in every response sit in one shared layer. That way every channel gives the same answer and people can use the model where they already work.

### 2. What is MCP, and when would you use MCP vs a plain REST API?

<details><summary>Understand it</summary>

```text
MCP (MODEL CONTEXT PROTOCOL)
An open protocol for connecting AI applications (hosts like Claude Desktop, IDEs, agent frameworks) to tools, resources and prompts. A server describes its tools (name, description, JSON-schema parameters); any MCP-capable host can discover and call them. Transports: stdio (local child process) and HTTP (streamable HTTP/SSE).

MCP IS GOOD FOR
- Making tools available to many AI hosts without custom integration per host.
- Tool discovery and rich descriptions aimed at models.
- Local tools (files, databases) via stdio.

REST IS GOOD FOR
- Non-AI clients: Excel, BI tools, web apps, other services, scripts.
- Mature infrastructure: gateways, caching, auth standards, monitoring, OpenAPI tooling.

BOTH
Write tools once as MCP, expose REST via a gateway (mcpo) or vice versa (wrap REST endpoints as MCP tools). Keep the business logic in neither: in a shared library/service behind both.

INTERVIEW LINE
'MCP is how models find and call tools; REST is how everything else does. We used both over one implementation.'
```

</details>

**Answer:** MCP is an open protocol that lets AI hosts like desktop assistants, IDEs and agent frameworks discover and call tools from a server, with schemas and descriptions written for models, over stdio locally or HTTP remotely. I'd use MCP to make tools available to many AI hosts without custom integrations, and REST for everything else: Excel, BI, web apps and services, where gateways, caching, auth and OpenAPI tooling are mature. In practice I write the logic once and expose both, for example MCP tools turned into REST endpoints by a gateway like mcpo.

### 3. Batch scoring or real-time serving? How do you decide?

<details><summary>Understand it</summary>

```text
REAL-TIME (online) SERVING
Compute the prediction when asked. Needed when inputs arrive at request time (user text, live prices) or the space of inputs is too big to precompute. Costs: latency budget, always-on compute, scaling.

BATCH (offline) SCORING
Compute predictions on a schedule (nightly) for all entities/dates and store them; the API just looks them up. Fast, cheap, reproducible, easy to audit. Fits when inputs change on a schedule (daily market data) and the entity set is known (all funds, all cohorts).

HYBRID
Precompute the heavy part (features, daily scores) in batch; do light work online (filtering, ranking for this user, formatting).

FOR AN ANALYST ASSISTANT
Daily data -> batch-score each day, store with model version and as-of date; tools read the stored scores. The chat stays fast, and every number is reproducible.
```

</details>

**Answer:** Real-time serving computes the prediction on request, which is necessary when inputs arrive at request time, like user text or live prices, but costs latency and always-on compute. Batch scoring computes predictions on a schedule for every entity and stores them, so the API just looks them up: fast, cheap, reproducible and auditable, and ideal for daily data. Often it's hybrid: heavy work in batch, light filtering online. For an analyst assistant on daily market data I'd batch-score each day with the model version and as-of date, and have the tools read the stored scores.


## API design

### 4. How do you version an API without breaking existing clients?

<details><summary>Understand it</summary>

```text
BREAKING VS NON-BREAKING
Non-breaking: adding endpoints, optional parameters, new response fields.
Breaking: removing/renaming fields or endpoints, changing types or units or meaning, new required parameters, different error formats.

STRATEGY
1. Version in the path (/v1, /v2) or header; path is simplest for spreadsheets and scripts.
2. A published version never changes shape. Improvements that break go to the next version.
3. Run versions side by side from the same implementation (v1 is an adapter over the new logic).
4. Deprecate politely: announce, add Deprecation/Sunset/Link headers, track who still calls v1 (API keys make this possible), contact them, then remove after the sunset date.
5. Enforce in CI: diff the OpenAPI schema against a committed snapshot; breaking changes fail the build (day17_product/contract_check.py).
6. Changelog for every release.

UNITS AND MEANING
The sneakiest breaking change keeps the field name but changes the meaning (decimal -> percent, calendar days -> business days). Put units in names (predicted_return_pct) and examples in docs.
```

</details>

**Answer:** Adding endpoints, optional parameters or response fields is safe; removing or renaming fields, changing types, units or meaning, or adding required parameters breaks clients. So I version in the path, a published version never changes shape, and breaking improvements go to the next version, running side by side over the same logic. Deprecation is announced with Deprecation and Sunset headers, and because every client has its own key I know who still calls the old version and can contact them before removal. CI diffs the OpenAPI schema against a snapshot to block accidental breaks, and units go in field names, because a silent decimal-to-percent change is the sneakiest break.

### 5. What makes a good error response from a model API?

<details><summary>Understand it</summary>

```text
GOOD ERRORS
- Correct status code: 400/422 bad input, 401 no/invalid auth, 403 not allowed, 404 not found, 409 conflict, 429 rate limited (with Retry-After), 500 our bug, 503 dependency down.
- A stable machine-readable code ('INVALID_ARGUMENT', 'NOT_A_BUSINESS_DAY') plus a human message that says how to fix it ('Try a nearby weekday').
- Never a stack trace, internal hostnames or SQL.
- A request/trace ID so support can find the logs.
- Documented in OpenAPI.

FOR AI TOOLS SPECIFICALLY
Tool errors should be returned as data the model can read and act on ('No data for 2025-06-21 (not a business day?). Try a nearby weekday.'), so the agent can recover by retrying with a valid date instead of failing the whole conversation.

CLIENT SIDE
Retry only retryable errors (429, 5xx) with backoff; never retry 4xx mistakes (day17_product/client.py).
```

</details>

**Answer:** A correct status code, like 422 for bad input, 401 or 403 for auth, 429 with Retry-After for rate limits and 503 when a dependency is down; a stable machine-readable error code plus a human message that says how to fix it; a trace ID; and never a stack trace or internal details. For AI tools specifically, errors should be readable data, like 'not a business day, try a nearby weekday', so the agent can recover by retrying with a valid date. Clients retry only 429 and 5xx with backoff, never 4xx mistakes.

### 6. How do you design a tool's interface so an LLM uses it correctly?

<details><summary>Understand it</summary>

```text
THE MODEL ONLY SEES THE NAME, DESCRIPTION AND SCHEMA
So write them for the model.

RULES
1. Name: verb + object, specific: rank_funds, get_fund_info. Not 'query' or 'helper'.
2. Description: what it does, when to use it, when NOT to use it, what it returns, units. 'Returns predicted 20-trading-day return as a decimal (0.0099 = 0.99%).'
3. Parameters: few, typed, constrained (enum, pattern YYYY-MM-DD, ranges), with descriptions and defaults.
4. Narrow over general: several clear tools beat one 'do anything' tool (also safer).
5. Output: compact, structured, with the as-of date and caveats; don't dump huge payloads into the context window.
6. Errors: as readable data with a hint to fix.
7. Idempotent read tools; side-effecting tools clearly named and gated.

TEST IT
Eval set of questions -> expected tool + arguments; measure tool-selection accuracy; read traces for confusions and fix descriptions.
```

</details>

**Answer:** The model only sees the name, description and schema, so I write them for the model: a specific verb-object name, a description of what it does, when to use it and not use it, what it returns and in what units, few typed and constrained parameters with patterns, enums and ranges, and narrow tools rather than one general one, which is also safer. Outputs are compact and structured with the as-of date and caveats, errors are readable hints, and I measure tool-selection accuracy on an eval set and fix descriptions where traces show confusion.


## Spreadsheet users

### 7. How would you deliver model outputs to analysts who work in Excel?

<details><summary>Understand it</summary>

```text
OPTIONS (simple to rich)
1. CSV/Excel file drops (email/SharePoint): simple, but stale and uncontrolled copies.
2. Data > From Web / Power Query against a REST endpoint (JSON or CSV): refreshable, no install; credentials in data source settings or a header.
3. An Office add-in (Office.js) or custom functions (=MODEL.RANK("2025-06-19")) calling the API: best UX, needs deployment and versioning.
4. Python in Excel / xlwings for power users.

DESIGN POINTS
- Same API as everyone else; units explicit; model version and as-of date in the output so a pasted table still says what produced it.
- Auth per user (SSO) or per team key; never keys inside shared workbooks.
- Performance: aggregate on the server; small payloads; caching.
- Release process: add-in versions tested in UAT before rollout; a way to see which version a user has.
- Support: a test workbook, documentation, and a way to report problems with the trace ID.
```

</details>

**Answer:** From simple to rich: file drops, which go stale; Power Query or From Web against a REST endpoint, which is refreshable with no install; an Office add-in or custom functions calling the API, which give the best experience but need deployment and versioning; or Python in Excel for power users. Whatever the channel, it uses the same API, with explicit units and the model version and as-of date in the output, auth per user or team with no keys in shared workbooks, small server-side aggregated payloads, and add-in releases tested in UAT before rollout.

### 8. What is an API gateway, and what does it do for a model platform?

<details><summary>Understand it</summary>

```text
WHAT
A layer in front of your services that every request passes through. Examples: Kong, Apigee, AWS API Gateway, GCP API Gateway/Cloud Endpoints, Nginx/Envoy; and for MCP, a gateway like mcpo that translates MCP tools to REST/OpenAPI.

JOBS
- Routing: /v2/rank -> model service; /chat -> agent service.
- Auth: validate tokens/keys once, centrally.
- Rate limiting and quotas per client.
- TLS termination, request size limits, WAF rules.
- Logging, metrics, tracing headers.
- Transformation: protocol translation (MCP <-> REST), version adapters.
- Caching of expensive, cacheable responses.

LLM GATEWAYS (a related idea)
A gateway in front of LLM providers: one API for many providers, key management, budgets per team, fallbacks, caching, logging (LiteLLM, Portkey, cloud AI gateways). Same idea as a vendor-neutral adapter, run as a service.
```

</details>

**Answer:** An API gateway is a layer every request passes through, handling routing, central auth, rate limits and quotas per client, TLS, request limits, logging and tracing, caching, and transformations like protocol translation. For a model platform that means one consistent front door to many services; an MCP-to-REST gateway like mcpo is a specific case that exposes MCP tools as OpenAPI endpoints. A related idea is an LLM gateway in front of model providers, with one API, per-team budgets, fallbacks and logging, which is a vendor-neutral adapter run as a service.


## LLM layer

### 9. Why build a vendor-neutral LLM layer, and how?

<details><summary>Understand it</summary>

```text
WHY
- Switch or mix providers/models by config (cost, quality, outages, client requirements, data residency).
- Failover when a provider is down (Day 8).
- One place for retries, timeouts, logging, cost tracking, redaction, prompt caching.
- Avoid business logic scattered across vendor SDK calls.
- Testability: a fake implementation for tests.

HOW
- Define your own interface: complete(system, messages, tools) -> {text, tool_calls, usage}.
- Implement adapters per provider (HTTP via httpx, or SDKs inside the adapter only).
- Normalise messages, tool-call formats, usage/cost, errors (retryable vs fatal).
- Configure model choice per task (routing) via config, not code.
- Enforce the boundary: a lint rule/import check that forbids vendor SDK imports outside the adapter.

TRADE-OFFS
Lowest-common-denominator risk: provider-specific features (prompt caching, structured outputs, extended thinking) need explicit support in the interface. Or use a maintained gateway (LiteLLM) instead of writing your own.
```

</details>

**Answer:** It lets me switch or mix providers by config for cost, quality, outages or client requirements, fail over when one is down, and keep retries, timeouts, logging, cost tracking and redaction in one place, plus a fake implementation for tests. I define my own interface, like complete with system, messages and tools returning text, tool calls and usage, write one adapter per provider that normalises messages, tool calls, usage and errors, choose models per task in config, and enforce the boundary with a lint rule that forbids vendor SDK imports outside the adapter. The trade-off is that provider-specific features need explicit support, or you use a maintained gateway like LiteLLM.

### 10. How do you route requests between models to balance cost and quality?

<details><summary>Understand it</summary>

```text
APPROACHES
1. Rules: task type -> model (definitions and classification -> small model; multi-step reasoning, tool planning -> large model).
2. Classifier router: a cheap model or classifier predicts difficulty/intent, then picks.
3. Cascade: try the small model; if confidence/validation fails (schema invalid, guard fails, low judge score), escalate to the large one.
4. User/tenant tiers and budgets.

MEASURE
Per route: quality (evals, guard pass rate), latency, cost per request. A route change is a deploy: eval + canary.

EXAMPLE
Day 12 simulation: definition questions on the small model, ranking/analysis on the large one. Lab question: what would routing all definitions to the small model save per month?
```

</details>

**Answer:** With rules by task type, small models for definitions and classification and large ones for reasoning and tool planning; or a cheap classifier that predicts difficulty; or a cascade where the small model answers first and the request escalates if validation or the guard fails; plus tiers and budgets per tenant. I measure quality, latency and cost per route, and treat a routing change like any deploy, with evals and a canary.


## Operating the product

### 11. How do you know who uses your model API and how much? Why does it matter?

<details><summary>Understand it</summary>

```text
HOW
- An identity per client: API keys or OAuth clients per team/app/user.
- Per-request logs/metrics with client id, endpoint, version, status, latency, cost.
- Dashboards: requests per client per day, error rates per client, versions in use.

WHY
- Deprecation: you can see who still calls /v1 and talk to them before removing it.
- Capacity planning and cost allocation (chargeback per team).
- Abuse/limits: quotas per client; revoke one key without affecting others.
- Product decisions: which outputs are used, which never are.
- Support: 'my numbers look wrong' -> find their requests by client id and trace id.
```

</details>

**Answer:** Every client gets its own identity, an API key or OAuth client, and every request is logged with the client, endpoint, version, status, latency and cost, feeding dashboards of usage, errors and versions in use. It matters because it shows who still calls an old version before deprecation, supports capacity planning and cost chargeback, lets me set quotas and revoke one key without affecting others, tells me which outputs are actually used, and lets support find a user's exact requests when they report a problem.

### 12. What documentation does a model API need?

<details><summary>Understand it</summary>

```text
MINIMUM
1. OpenAPI reference generated from code (FastAPI /docs): endpoints, parameters, schemas, errors, auth.
2. Quick start: get a key, first call in curl, Python and Excel.
3. Semantics: what each output means, units, horizon, as-of rules (which data is used for a date), caveats ('research signal, not advice').
4. Model card: what the model is, training data period, validation results honestly reported, known limitations, version history.
5. Changelog and deprecation policy.
6. Limits: rate limits, quotas, payload sizes, latency expectations.
7. Support: how to report issues (include the trace id).

WHY IT MATTERS
Most 'bugs' reported by model users are misunderstandings of meaning or timing. Good semantics docs prevent them.
```

</details>

**Answer:** An OpenAPI reference generated from the code, a quick start with a first call in curl, Python and Excel, and clear semantics: what each output means, units, horizon, which data is used for a given date, and caveats. A model card with the training period, honestly reported validation and known limitations, plus version history. Then a changelog and deprecation policy, limits, and a support path that asks for the trace ID. Most reported bugs are really misunderstandings of meaning or timing, so semantics docs matter most.


## Scenarios

### 13. An Excel user says the numbers changed overnight. How do you investigate?

<details><summary>Understand it</summary>

```text
QUESTIONS
1. Which numbers, which date (as_of), which version of the add-in/query?
2. Did the model version change? (Every response carries model_version.)
3. Did the input data change? Revisions or late-arriving data for that as-of date, a backfill, a fixed bug in the pipeline.
4. Did the API contract change? Units (decimal vs percent), default parameters (top_n, model), rounding.
5. Is their query asking for 'latest' (as_of empty) rather than a fixed date, so it naturally moves each day?
6. Caching: stale vs fresh.

HOW
Find their requests by API key/trace id; compare responses for the same parameters across days; check the deploy log, the pipeline run log and the data's ingested_at for that period.

PREVENT
Show model_version and as_of_used in the sheet; pin dates in reports; announce model changes; contract checks for units.
```

</details>

**Answer:** I ask which numbers, which as-of date and which add-in or query version, then look at their actual requests by API key and trace ID and compare responses for the same parameters across days. The usual causes are a new model version, data revisions or a backfill for that date, a contract change like units or defaults, or a query asking for 'latest' so it naturally moves daily. I check the deploy log, pipeline runs and load times for that period. To prevent confusion, sheets show the model version and as-of date, reports pin dates, and model changes are announced.

### 14. Design a platform to serve several proprietary models to internal and client users.

<details><summary>Understand it</summary>

```text
LAYERS
1. Models: each model packaged with a version, validated, with a model card; batch scores stored with model version + as-of date; real-time where needed.
2. Model services: one service (or one MCP server) per model family with narrow, typed tools/endpoints.
3. Gateway: auth (SSO for users, keys for clients), quotas, routing, MCP-to-REST translation, logging.
4. Channels: AI agent (MCP), Excel (add-in/Power Query), notebooks (client library), partner services (REST/OpenAPI).
5. LLM layer (for the assistant): vendor-neutral adapter, routing, guards, tracing.
6. Data: point-in-time stores feeding models; freshness monitoring.
7. Delivery: CI with contract checks and evals; versioned releases; dev -> UAT -> prod; canaries; rollback.
8. Ops: usage per client, SLOs, alerts, audit logs, documentation and changelog.

PRINCIPLES
One implementation per model, many channels; explicit units and dates; backward-compatible versions; honest documentation of model limits.
```

</details>

**Answer:** Each model is versioned and validated with a model card, with batch scores stored by model version and as-of date. Each model family gets a service or MCP server with narrow typed tools, behind a gateway that handles SSO and client keys, quotas, routing, MCP-to-REST translation and logging. Channels on top: the AI agent through MCP, Excel through an add-in or Power Query, notebooks through a client library, partners through REST with OpenAPI. The assistant uses a vendor-neutral LLM layer with guards and tracing. Underneath are point-in-time data stores with freshness monitoring, and around it CI with contract checks and evals, dev, UAT and prod with canaries, plus usage dashboards, SLOs and audit logs.


## Glossary

| Term | Meaning |
|---|---|
| MCP | Model Context Protocol: open standard for AI hosts to discover and call tools. |
| mcpo / MCP-to-REST gateway | Exposes MCP tools as REST endpoints with OpenAPI. |
| OpenAPI | Machine-readable API description; generates docs and clients. |
| Breaking change | A change that can break existing clients (removed/renamed field, type/unit change). |
| Deprecation / Sunset headers | HTTP headers announcing an endpoint is deprecated and when it will be removed. |
| Contract snapshot | A committed copy of the API schema that CI diffs against. |
| Batch scoring | Precomputing predictions on a schedule and serving lookups. |
| Online serving | Computing predictions at request time. |
| API gateway | Front door for services: auth, routing, quotas, logging, translation. |
| LLM gateway | One API in front of many LLM providers: keys, budgets, fallbacks, logs. |
| Vendor-neutral adapter | Your own LLM interface with one implementation per provider. |
| Model routing / cascade | Choosing a model per request / escalating from small to large on failure. |
| Power Query | Excel's data import/transform engine; can call REST APIs. |
| Office add-in | Excel extension (Office.js) that can add custom functions and panes. |
| Model card | Document of what a model is, its data, validation, limits and versions. |
| Retry with backoff | Re-try transient failures with growing waits; never retry 4xx. |
