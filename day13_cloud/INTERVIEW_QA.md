# Interview questions: Cloud deployment for AI services

For each question: open **Understand it** and read until it is clear, then say the **Answer** out loud in 30-45 seconds.
Code for the ideas is in this folder; the hands-on steps are in [LAB.md](LAB.md).


## Cloud basics

### 1. How would you deploy an LLM application to the cloud? Walk me through it end to end.

<details><summary>Understand it</summary>

```text
THE PIPELINE (say it in this order)
1. Code merged to main through a pull request with CI green (tests, lint, types, evals).
2. CI builds ONE Docker image, tagged with the git commit (main-ce57d87), and pushes it to a registry (Artifact Registry, ECR, ACR, Docker Hub).
3. The image is deployed to a compute service: a managed container platform (Cloud Run, App Runner, Azure Container Apps), Kubernetes, or a plain VM with Docker.
4. Config comes from environment variables; secrets from a secrets manager. Nothing secret in the image or in Git.
5. HTTPS in front: the platform's own TLS, or Nginx + Let's Encrypt on a VM, or a cloud load balancer.
6. State lives outside the containers: a managed database (Cloud SQL / RDS Postgres), object storage for files, a managed vector store or pgvector.
7. Release safely: deploy the new version with no traffic, smoke test it, canary 5-10%, compare metrics, promote or roll back.
8. Observe: logs, metrics, traces, alerts (Day 12).

WHY THIS ORDER MATTERS
Each step removes one class of failure: untested code (CI), 'works on my machine' (image), drift between environments (same image everywhere), leaked secrets (secret manager), outages from bad releases (canary + rollback), lost data (managed DB + backups).
```

</details>

**Answer:** Code goes in through a PR with CI green, then CI builds one image tagged with the commit and pushes it to a registry. I deploy that same image to a managed container service like Cloud Run, or a VM with Docker for simpler setups, with config from environment variables and secrets from a secrets manager. HTTPS sits in front, and all state lives in a managed database outside the containers. Releases go out with no traffic first, get a smoke test, then a small canary, and are promoted or rolled back on metrics, with monitoring and alerts throughout.

### 2. VM, managed containers (Cloud Run) or Kubernetes: how do you choose?

<details><summary>Understand it</summary>

```text
THE THREE OPTIONS
1. VM with Docker (Compute Engine, EC2)
   + Full control, simple to understand, predictable cost, GPUs easy, long-running processes fine.
   - You patch the OS, set up TLS, restarts, scaling and deploy scripts yourself. Scaling is manual.
2. Managed containers / serverless containers (Cloud Run, AWS App Runner, Azure Container Apps)
   + Give it an image, get an HTTPS URL. Autoscaling (to zero if you want), revisions, traffic splitting, per-request billing.
   - Request timeouts, cold starts, less control, GPUs limited, background work needs care.
3. Kubernetes (GKE, EKS, AKS)
   + Most flexible: many services, custom networking, GPUs, operators, batch jobs, service mesh.
   - Steep learning curve and real operations cost. Overkill for a few services and a small team.

DECISION RULE
- One to a few stateless HTTP services, small team: managed containers.
- Need full control, GPUs, unusual networking, or a fixed internal tool: a VM.
- Many services, a platform team, complex scheduling or GPU fleets: Kubernetes.

LLM-SPECIFIC
If you CALL a model API, your service is mostly I/O waiting: managed containers fit well (set concurrency high).
If you HOST a model (vLLM on GPUs), you need GPU nodes: VMs or Kubernetes, or a managed inference service.

INTERVIEW TIP
Say what you'd start with and when you'd move: 'Cloud Run first; Kubernetes when we have many services and someone to run it.'
```

</details>

**Answer:** It depends on team size and needs. A VM with Docker gives full control and easy GPUs, but I own patching, TLS, restarts and scaling. Managed containers like Cloud Run give an HTTPS URL from an image, with autoscaling, revisions and traffic splitting, at the cost of timeouts, cold starts and less control. Kubernetes is the most flexible but has real operating cost, so it fits many services and a platform team. For an app that calls an LLM API I'd start on managed containers; if we host our own model on GPUs, VMs or Kubernetes.

### 3. What is a container registry, and why tag images by git commit?

<details><summary>Understand it</summary>

```text
REGISTRY
A storage service for Docker images: Artifact Registry (GCP), ECR (AWS), ACR (Azure), Docker Hub, GitHub Container Registry. CI pushes images there; servers pull from there. Access is controlled by IAM.

TAGS
A tag is a human label on an image: model-service:latest, model-service:v1.4, model-service:main-ce57d87.
'latest' is just a word: it moves every time someone pushes. Two servers pulling 'latest' an hour apart can run different code.

WHY TAG BY COMMIT
- Traceability: from a running container you know the exact code (git show ce57d87).
- Reproducibility: redeploy exactly that version later.
- Rollback: the previous commit's image is still in the registry; switch back with no rebuild.
- Promotion: dev and prod run the same tag, so prod runs what dev tested.

EVEN STRONGER: DIGESTS
A digest (sha256:...) identifies the exact image content and can never move. Pin by digest for maximum safety. Gotcha from real life: different Docker versions can show different kinds of digest for the same image (manifest vs config), so compare like with like.

HYGIENE
Lifecycle rules to delete old untagged images (storage costs), vulnerability scanning on push, immutable tags if the registry supports it.
```

</details>

**Answer:** A registry stores Docker images: CI pushes, servers pull, and IAM controls access. I tag images with the git commit instead of 'latest', because 'latest' moves and two servers can end up running different code. A commit tag tells me exactly what code is running, lets me redeploy or roll back to any version without rebuilding, and lets dev and prod run the identical image. For maximum safety I pin by digest, and I add vulnerability scanning and cleanup rules for old images.


## Config and secrets

### 4. How do you manage configuration and secrets in the cloud?

<details><summary>Understand it</summary>

```text
CONFIG VS SECRETS
- Config: things that differ between environments but aren't sensitive: model name, log level, database host, feature flags. Environment variables or a config file in the deploy repo.
- Secrets: API keys, database passwords, signing keys. Must never be in Git, in the image, or in logs.

WHERE SECRETS LIVE
A secrets manager: GCP Secret Manager, AWS Secrets Manager / Parameter Store, Azure Key Vault, HashiCorp Vault. On a single VM: a root-owned env file with chmod 600 is acceptable but weaker.

HOW THE APP GETS THEM
- The platform injects them as env vars or mounted files at start (Cloud Run --set-secrets API_KEY=api-key:latest).
- The runtime service account has permission to read ONLY the secrets it needs (least privilege).

ROTATION
- Add a new secret version, deploy a new revision/container so it's read, VERIFY it's live, then disable the old version.
- Real trap: on Docker, 'docker restart' reuses the env from creation. On Cloud Run, a running revision keeps the version it resolved; a new revision picks up the new one.

NEVER
- Print env values in logs or debug output (connection URLs often embed passwords).
- Pass secrets as command-line arguments (visible in process lists and shell history).
- Bake them into images (layers can be extracted).
```

</details>

**Answer:** Config that isn't sensitive, like the model name or log level, goes in environment variables per environment. Secrets live in a secrets manager like Secret Manager or Key Vault and are injected at start, and the service account can read only the secrets it needs. To rotate, I add a new version, deploy a new container or revision so it's actually read, verify it's live, then disable the old one. I never put secrets in Git, images, command-line arguments or logs, and I never print env values, because connection URLs often embed passwords.

### 5. How does a CI pipeline deploy to the cloud without storing a cloud key?

<details><summary>Understand it</summary>

```text
THE OLD WAY (avoid)
Create a service account JSON key, paste it into GitHub Secrets. Problems: a long-lived credential that can leak, is hard to rotate, and works from anywhere.

THE MODERN WAY: WORKLOAD IDENTITY FEDERATION (OIDC)
1. GitHub Actions can issue a short-lived signed token (OIDC) that says 'I am workflow X in repo Y on branch main'.
2. The cloud (GCP Workload Identity Federation, AWS IAM OIDC provider, Azure federated credentials) is configured to trust GitHub's issuer, and only for that repo/branch.
3. The workflow exchanges the token for short-lived cloud credentials (minutes), then deploys.
No stored key; nothing to leak or rotate; access limited to that repo and branch.

IN THE WORKFLOW
permissions: id-token: write
uses: google-github-actions/auth@v2 with workload_identity_provider and service_account

ALSO
- The deploy service account gets only deploy permissions (Cloud Run admin on one service, push to one registry).
- Protect the production environment in GitHub with required reviewers for a manual approval gate.
```

</details>

**Answer:** With workload identity federation. GitHub Actions issues a short-lived OIDC token that says which repo and branch it's running for; the cloud is configured to trust only that repo and branch and swaps the token for credentials that expire in minutes. So there's no long-lived JSON key in GitHub to leak or rotate. The deploy identity gets only the permissions it needs, and I protect the production environment with required reviewers.


## Releases

### 6. What is a canary release? Compare blue/green, rolling and canary.

<details><summary>Understand it</summary>

```text
ROLLING
Replace instances a few at a time. Simple, built into most platforms. During the rollout both versions serve traffic; rollback means rolling again.

BLUE/GREEN
Run the full new version (green) next to the old (blue). Switch all traffic at once. Instant rollback: switch back. Costs double capacity during the switch.

CANARY
Send a small share (1-10%) of real traffic to the new version, compare its metrics with the old one, then increase step by step or roll back. Limits the blast radius of a bad release to a few users.

FOR LLM APPS, CANARY IS USUALLY BEST
Many LLM regressions only show on real traffic (quality, cost, latency on real prompts). Compare:
- error rate, p95 latency, cost per request
- quality: answer-check pass rate, thumbs-down (Day 12)
Write the promotion rule BEFORE the rollout (day13_cloud/canary.py): minimum requests, allowed error increase, allowed latency increase, allowed quality drop.

ON CLOUD RUN
deploy --no-traffic --tag canary -> smoke test the tag URL -> update-traffic --to-tags canary=10 -> --to-latest or roll back to the old revision.

SINGLE VM VERSION
Old container renamed and kept; new one started; smoke test; auto-rollback on failure (vm/deploy_vm.sh).
```

</details>

**Answer:** Rolling replaces instances gradually; blue/green runs the whole new version beside the old and switches traffic at once with instant rollback; canary sends a small share of real traffic to the new version, compares metrics, then increases or rolls back. For LLM apps I prefer canary, because quality, cost and latency regressions often show only on real prompts. I write the promotion rule beforehand: minimum traffic, and limits on error rate, p95 latency and answer-quality drop. On Cloud Run that's deploy with no traffic, smoke test, then 10 percent.

### 7. What is a smoke test, and why isn't a health check enough?

<details><summary>Understand it</summary>

```text
HEALTH CHECK
/health returns ok if the process is up. The platform uses it to restart crashed containers and to route traffic only to ready ones (liveness vs readiness).

WHAT IT CAN'T TELL YOU
- That the NEW version is the one running (the old container may still be serving).
- That the secret or config is correct.
- That the model actually loads and answers correctly.
- That the database and external APIs are reachable with the right credentials.

SMOKE TEST
A small set of real end-to-end checks run right after deploy against the real URL:
1. health ok and fast
2. /config or /version reports the version we meant to ship
3. secrets present (yes/no only, never values)
4. one real model call returns a known answer
5. a bad input returns a clean error
Exit code non-zero -> the pipeline rolls back automatically.

DAY 13 LAB
Deploy B: health ok, but old version running and key missing. The smoke test fails it; a health check alone would have passed it.
```

</details>

**Answer:** A health check only says the process is alive, which the platform uses to restart and route. It can't tell me the new version is the one serving, that secrets and config are right, or that the model answers correctly. A smoke test runs a few real checks against the live URL right after deploy: health, the version matches what we shipped, secrets present without revealing values, a known model answer, and a clean error on bad input. A failure exits non-zero and the pipeline rolls back. In my lab, a stale deploy passes the health check and fails the smoke test.

### 8. How do you roll back a bad deployment quickly?

<details><summary>Understand it</summary>

```text
PREPARE BEFORE YOU NEED IT
- Keep the previous version runnable: old revision (Cloud Run), old ReplicaSet (Kubernetes), old container renamed (VM), old image in the registry (always).
- Make rollback ONE command, documented, and practised.
- Keep database changes backward compatible (see migrations question), or rollback of code breaks on the new schema.

HOW, BY PLATFORM
- Cloud Run: gcloud run services update-traffic SERVICE --to-revisions OLD=100 (seconds).
- Kubernetes: kubectl rollout undo deployment/SERVICE.
- VM: docker rm -f svc && docker rename svc-previous svc && docker start svc.
- Prompt or model config: switch the version flag back (Day 12).

WHEN
Mitigate first, diagnose later. If a release correlates with a problem, roll back first, then investigate calmly.

AFTER
Verify the rollback worked (smoke test), communicate, postmortem.
```

</details>

**Answer:** I prepare before I need it: the previous version stays runnable, as an old revision, an old ReplicaSet or a renamed container, and its image stays in the registry, so rollback is one documented command: update traffic back to the old revision on Cloud Run, rollout undo on Kubernetes, or swap the containers on a VM. Database migrations stay backward compatible so old code still works. When a release correlates with a problem I roll back first and investigate after, then verify with the smoke test.

### 9. How do you handle database migrations during deploys without downtime?

<details><summary>Understand it</summary>

```text
THE PROBLEM
During a rollout, old and new code run at the same time, and you may need to roll back. If the new code renames a column, the old code breaks immediately.

EXPAND / CONTRACT (parallel change)
1. Expand: add the new column/table; keep the old one. Deploy code that writes both and reads the old.
2. Backfill: copy existing data into the new column, in batches, idempotently.
3. Switch reads to the new column. Monitor.
4. Contract: once nothing uses the old column (and rollback to old code is no longer needed), remove it in a later release.

RULES
- Every migration is backward compatible with the currently running code.
- Migrations are versioned in Git (Alembic, Flyway, Liquibase) and run as a separate step before the code deploy.
- Take a backup or confirm PITR before risky migrations.
- Big backfills in batches with throttling; they can overload the database (and did, in a real dev outage).

INTERVIEW LINE
'Never couple a breaking schema change and the code that needs it in one deploy.'
```

</details>

**Answer:** I use expand and contract. First add the new column or table without removing the old one, and deploy code that writes both. Then backfill in batches, switch reads to the new structure, and only in a later release drop the old one. Every migration stays compatible with the code currently running, so rolling updates and rollbacks don't break. Migrations are versioned with something like Alembic, run as a separate step, and I confirm a backup or point-in-time recovery first. Big backfills are throttled, because they can overload the database.


## State and data

### 10. Where should state live in a cloud AI application?

<details><summary>Understand it</summary>

```text
RULE: CONTAINERS ARE CATTLE, NOT PETS
Any container can be killed, replaced or scaled at any moment. So nothing important may live only inside one.

WHERE EACH KIND OF STATE GOES
- Conversations, users, agent checkpoints: managed Postgres (Cloud SQL, RDS). LangGraph checkpointing can store agent state in Postgres so any replica can continue a thread.
- Documents and files: object storage (GCS, S3).
- Embeddings: pgvector in the same Postgres, or a managed vector database.
- Cache and rate-limit counters: Redis/Memorystore (losing it is OK).
- Model weights: baked into the image if small, or object storage / a model registry if large.
- Logs, traces, metrics: the observability stack, not local files.

WHY MANAGED DATABASES
Backups, PITR, patching, failover and encryption handled for you. Running Postgres in a container on a VM disk works but puts all of that on you.

STATELESS SERVICE BENEFITS
Scale horizontally, deploy with rolling/canary, restart freely, run in any zone.
```

</details>

**Answer:** Nothing important should live only inside a container, because containers get replaced and scaled at any time. Conversations, users and agent checkpoints go in managed Postgres, so any replica can continue a thread. Files go in object storage, embeddings in pgvector or a vector database, caches in Redis where losing them is fine, and logs and traces in the observability stack. Managed databases give me backups, point-in-time recovery, patching and failover. That keeps the services stateless, so they scale and deploy freely.

### 11. Explain backups, point-in-time recovery, RPO and RTO.

<details><summary>Understand it</summary>

```text
BACKUPS
Full copies taken on a schedule (e.g. daily at 02:00), kept for N days. Restore = go back to the moment of a backup. If the last backup was 22 hours ago, you lose up to 22 hours.

POINT-IN-TIME RECOVERY (PITR)
The database also keeps its transaction log (write-ahead log). Restore = latest backup + replay the log up to any second you choose, e.g. 09:41:00, just before the bad migration at 09:42. Costs some storage; must be switched on.

RPO AND RTO
- RPO (recovery point objective): how much data you can afford to lose. Daily backups -> RPO up to 24 h. PITR -> minutes or seconds.
- RTO (recovery time objective): how long until you're back up. Depends on database size and practice.

PRACTICE
A backup you've never restored is a hope. Run restore drills: clone the database to a point in time, check the data, measure the time, delete the clone.

DECISION
Production data that matters: daily backups AND PITR, with retention that covers how late you might notice a problem. Dev: PITR is a cheap way to undo mistakes too.
```

</details>

**Answer:** Backups are scheduled full copies, so restoring loses everything since the last one. Point-in-time recovery also keeps the transaction log, so I can restore to any second, like just before a bad migration. RPO is how much data I can afford to lose: up to a day with daily backups, seconds with PITR. RTO is how long the restore takes. For important production data I want both backups and PITR, and I run restore drills, cloning to a point in time and timing it, because a backup that's never been restored is just a hope.


## Networking and security

### 12. How do you put HTTPS in front of a service?

<details><summary>Understand it</summary>

```text
WHY
Encryption in transit (nobody on the network can read prompts, answers or tokens), server identity (the client knows it's really you), and browsers/clients require it.

OPTIONS
1. Managed platform: Cloud Run, App Runner and similar give you HTTPS automatically, including custom domains.
2. Cloud load balancer with a managed certificate: good for many services, a WAF and global routing.
3. On a VM: Nginx (or Caddy, Traefik) as a reverse proxy with a free Let's Encrypt certificate via certbot, auto-renewed every ~60-90 days.

NGINX SETUP ESSENTIALS (vm/nginx_tls.conf)
- Port 80 only redirects to HTTPS (and serves the ACME challenge for renewals).
- Port 443 with the certificate, TLS 1.2/1.3, HSTS header.
- proxy_pass to the app on 127.0.0.1 only: the container is not reachable from outside directly.
- For LLM streaming: proxy_buffering off and a longer proxy_read_timeout.

COMMON FAILURES
Certificate renewal silently failing (test with certbot renew --dry-run, alert on expiry date), the app port exposed publicly next to Nginx, buffering breaking token streaming.
```

</details>

**Answer:** On managed platforms like Cloud Run HTTPS is automatic. On a VM I put Nginx in front as a reverse proxy with a free Let's Encrypt certificate from certbot, auto-renewed. Port 80 just redirects to HTTPS, port 443 terminates TLS with modern protocols and HSTS, and proxies to the app bound to localhost only, so the container is never exposed directly. For LLM streaming I turn proxy buffering off and raise the read timeout, and I alert on certificate expiry because silent renewal failures are common.

### 13. What is least privilege in the cloud, and how do you apply it to an AI service?

<details><summary>Understand it</summary>

```text
PRINCIPLE
Every identity (person, service, CI job) gets only the permissions it needs, on only the resources it needs, for only as long as it needs them.

APPLIED TO AN AI SERVICE
- The runtime service account: read ONE secret (its API key), connect to ITS database, read ITS bucket. Not project Editor.
- The CI deploy identity: push to one registry, deploy one service. Short-lived via OIDC.
- Humans: read-only in production by default; elevated access through a time-limited, logged request.
- Network: the database has no public IP, or only allows the service; the app listens on localhost behind the proxy.
- LLM tools: the agent's tools act with the user's permissions, not a super-user account (see the security day).

WHY
A leaked credential or a compromised container (or a prompt-injected agent) can only do what that identity can do. Least privilege limits the blast radius.

COMMON MISTAKES
Default compute service account with Editor role, one shared key for everything, public database IPs, 'temporary' admin grants that never expire.
```

</details>

**Answer:** Every identity gets only the permissions it needs on only the resources it needs. For an AI service, the runtime service account can read just its own secret, its database and its bucket, not project editor; the CI identity can push to one registry and deploy one service using short-lived OIDC credentials; humans are read-only in production by default; and the database isn't publicly reachable. The agent's tools act with the user's permissions. So a leaked key, a compromised container or a prompt-injected agent can only do limited damage.


## Scaling and cost

### 14. How do autoscaling, concurrency and cold starts work for an LLM service?

<details><summary>Understand it</summary>

```text
AUTOSCALING
The platform adds instances when load rises and removes them when it falls. Signals: requests in flight (Cloud Run), CPU, or custom metrics (queue length).

CONCURRENCY
How many requests one instance handles at once. An app that calls an LLM API spends most of each request WAITING for the provider (I/O bound). With async code one instance can serve dozens of requests concurrently. Setting concurrency to 1 would multiply instances and cost for no reason.

COLD STARTS
A new instance must start the container, import libraries and load models. Seconds for a small app, much longer if it loads large models. Users hitting a cold instance wait.
Mitigations: min instances (1 or more kept warm), smaller images, lazy imports, load models at startup not per request, startup CPU boost.

LIMITS ARE A FEATURE
max instances = a cost ceiling and protects downstream (database connections, provider rate limits). Database connection pools x instances must stay under the database's connection limit.

SELF-HOSTED MODELS ARE DIFFERENT
GPU instances are expensive and slow to start; scale on queue length/GPU utilisation, batch requests (vLLM continuous batching), and keep a warm minimum.
```

</details>

**Answer:** Autoscaling adds and removes instances based on load, such as requests in flight or CPU. Concurrency is how many requests one instance serves at once. A service that calls an LLM API mostly waits on I/O, so with async code one instance can handle dozens of requests, and low concurrency just multiplies cost. Cold starts are the delay when a new instance boots and loads libraries or models; I keep a minimum of warm instances and keep images small. Max instances is a cost ceiling and protects the database and provider rate limits. Self-hosted GPU models scale on queue length with batching.

### 15. How do you keep cloud costs under control for an AI application?

<details><summary>Understand it</summary>

```text
WHERE THE MONEY GOES
1. LLM API tokens (often the biggest line; see Day 12).
2. Compute: always-on instances, oversized VMs, idle GPUs.
3. Databases: instance size, storage, backups, PITR log storage, test clones left running.
4. Network egress and load balancers.
5. Logs: verbose logging of full prompts can cost real money in log storage.

CONTROLS
- Budgets and alerts in the cloud console (50%, 90%, 100% of monthly budget).
- Labels/tags on every resource (team, env, service) so the bill can be split.
- Right-size: check actual CPU/memory use; scale to zero for dev; max instances caps.
- Schedule dev/test environments off at night.
- Lifecycle rules: delete old images, old logs, old backups beyond retention.
- Committed-use/reserved discounts for steady baseline load.
- Clean up after experiments (database clones, test services).

HABIT
Review the bill monthly by service; treat a surprise as an incident.
```

</details>

**Answer:** First know where it goes: LLM tokens are often the biggest line, then always-on compute and idle GPUs, databases and their backups, egress and log storage. I set budgets with alerts at 50, 90 and 100 percent, label every resource by service and environment so the bill can be split, right-size based on actual usage, cap max instances, scale dev to zero or switch it off at night, set lifecycle rules for old images, logs and backups, and use committed-use discounts for steady load. I review the bill monthly and treat surprises like incidents.


## Scenarios

### 16. You deployed, and users say the new feature isn't there. What do you check?

<details><summary>Understand it</summary>

```text
LIKELY CAUSES, IN ORDER
1. The old version is still serving: deploy didn't finish, traffic still on the old revision, old container still bound to the port, a load balancer pointing at old instances.
2. Config not applied: the feature flag or env var is in the file but the container wasn't recreated (docker restart trap) or the new revision didn't get it.
3. Caching: a CDN, browser cache or app cache serving the old response.
4. Wrong environment: deployed to dev, users on prod; or a different region.
5. The image doesn't contain the change: built from the wrong commit or branch.

HOW TO CHECK FAST
- /config or /version on the live URL: which commit and settings are actually running?
- Cloud Run: which revision has traffic? Docker: docker ps, docker inspect (image ID, env, start time).
- Compare the image tag/digest with the commit that has the change (git log, git branch --contains).

PREVENT
Smoke test that asserts the version after every deploy; build from a fresh fetch of origin/main (a real story: a branch made from an old commit silently missed 19 merges).
```

</details>

**Answer:** First I check what is actually running: the version endpoint on the live URL, which revision has the traffic, and docker inspect for the image ID, env and start time. The usual causes are the old version still serving, config not applied because the container wasn't recreated, a cache serving old responses, deploying to the wrong environment, or an image built from the wrong commit. I compare the running tag with the commit that has the change. To prevent it, every deploy runs a smoke test that asserts the version.

### 17. Design the deployment for an AI research assistant for a financial firm.

<details><summary>Understand it</summary>

```text
ANSWER IN LAYERS

1. COMPUTE
Containerised services: chat/agent API, model tools (MCP servers) with a REST gateway for spreadsheet users, a knowledge/RAG service, background workers. Start on managed containers or a hardened VM; Kubernetes only when services multiply.

2. DATA
Managed Postgres for users, conversations and agent checkpoints (+ pgvector for embeddings); object storage for documents; a market-data pipeline writing point-in-time data. Daily backups + PITR; restore drills.

3. SECURITY
Private networking for the database; HTTPS everywhere; secrets in a secrets manager; least-privilege service accounts; server-side authentication and per-user authorisation; audit logs; data stays in the firm's region/cloud.

4. DELIVERY
PR + CI (types, lint, tests, API fuzzing, evals) -> one image per commit -> deploy to dev -> smoke test -> manual approval -> prod canary with written rules -> promote or roll back. The previous version always one command away.

5. OPERATIONS
OpenTelemetry traces, dashboards, alerts (including data freshness), on-call runbook, postmortems.

6. CLIENT DELIVERY
A UAT environment that mirrors prod, a UAT question catalogue signed off before go-live, and a change process the client trusts.
```

</details>

**Answer:** I'd containerise the services: the agent API, model tools as MCP servers with a REST gateway for spreadsheet users, a RAG service and background workers, on managed containers or a hardened VM to start. Data goes in managed Postgres with pgvector and agent checkpoints, documents in object storage, and point-in-time market data from a pipeline, with backups and PITR. Security means private database networking, HTTPS, a secrets manager, least privilege, server-side auth and audit logs, with data kept in the firm's region. Delivery is PR and CI with evals, one image per commit, dev, smoke test, approval, a prod canary and one-command rollback. Operations are OpenTelemetry, alerts including data freshness, and runbooks, plus a UAT environment and catalog before go-live.


## Glossary

| Term | Meaning |
|---|---|
| Container registry | Stores Docker images (Artifact Registry, ECR, ACR, Docker Hub). |
| Image tag / digest | Movable human label / immutable content hash of an image. |
| Cloud Run / App Runner | Managed container platforms: image in, HTTPS URL out, autoscaling. |
| Revision | An immutable deployed version of a Cloud Run service; traffic can be split between revisions. |
| Secrets manager | Stores and versions secrets with access control (Secret Manager, Key Vault, AWS Secrets Manager). |
| Workload Identity Federation | CI exchanges a short-lived OIDC token for cloud credentials; no stored key. |
| Least privilege | Each identity gets only the permissions it needs. |
| Smoke test | A few real end-to-end checks right after a deploy. |
| Canary | Send a small share of traffic to the new version, compare, then promote or roll back. |
| Blue/green | Run old and new side by side, switch all traffic at once. |
| Rolling update | Replace instances a few at a time. |
| Expand / contract | Backward-compatible schema change in steps: add, backfill, switch, remove. |
| PITR | Point-in-time recovery: restore a database to any second in the retention window. |
| RPO / RTO | How much data you can lose / how long recovery takes. |
| Reverse proxy | Nginx/Caddy in front of the app: TLS, routing, timeouts. |
| Let's Encrypt / certbot | Free TLS certificates and the tool that obtains and renews them. |
| Cold start | Delay while a new instance starts and loads code or models. |
| Concurrency | Requests one instance serves at the same time. |
| Min / max instances | Warm floor (no cold start) / cost and load ceiling. |
