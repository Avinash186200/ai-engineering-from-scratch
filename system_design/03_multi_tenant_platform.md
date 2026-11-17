# Design 3: an agent platform shared by many organisations

**Prompt**: "Build a platform where many separate companies (tenants) each configure their own assistant over their
own documents and tools."

## 1. Clarify (assumed answers)

- 500 tenants, from 5 users to 5,000 users each. A few large tenants generate most of the traffic.
- Tenants bring documents and connect some of their own APIs as tools.
- Strict isolation: one tenant's data must never appear in another's answer, logs or caches.
- Pricing tiers: free, standard, enterprise (enterprise may want its own model provider key).

## 2. Requirements

- Isolation, per-tenant cost reporting, quotas, per-tenant configuration (prompt, tools, model), audit per tenant.
- Noisy neighbours must not slow everyone else down.

## 3. Boxes

```
Request (tenant id from auth token) -> gateway (auth, quota, rate limit)
   -> agent runtime (loads tenant config) -> tools (tenant-scoped credentials) | retriever (tenant-scoped index) -> LLM router
   -> traces and usage metering tagged with tenant id
```

## 4. Deep dive: isolation

- **Tenant id everywhere**: on every row, chunk, cache key, trace and log line. It comes from the auth token, never
  from the request body or the model.
- **Indexes**: small tenants share an index with a mandatory tenant filter applied by the platform; large or
  regulated tenants get their own index. Tests try cross-tenant queries and must get nothing.
- **Caches**: keys include the tenant id; a semantic cache never crosses tenants.
- **Tool credentials**: stored per tenant in a secrets manager, injected at call time, never shown to the model.
- **Memory**: user memory and tenant-wide memory live in separate namespaces; nothing is promoted to shared memory
  without an explicit rule.

## 5. Fairness and cost

- Per-tenant quotas on requests and tokens; queues per tier so a large batch from one tenant does not starve others.
- Model routing by tier (cheaper model on the free tier) and by task difficulty.
- Usage metering from traces: tokens, tool calls and storage per tenant, which feeds billing and alerts.

## 6. Operations

- A platform-wide golden set plus optional tenant golden sets that run before a tenant's config change goes live.
- Config changes are versioned and can be rolled back per tenant.
- Canary platform releases to a few internal and free-tier tenants first.

## 7. Trade-offs and v1

- Shared index with filters is cheap but relies on code being right; separate indexes are safer but cost more.
  v1: shared with tests, separate for enterprise.
- Per-tenant prompts give flexibility but multiply what you need to evaluate; offer templates with limited knobs.

## Likely probes

- "How do you prove isolation?" Automated cross-tenant tests in CI, tenant filter enforced in one shared library,
  and audit logs showing every access with its tenant id.
- "An enterprise tenant wants to use its own provider key." The LLM adapter takes the provider and key from tenant
  config; usage for that tenant is then billed by the provider directly.
