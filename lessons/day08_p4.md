# Day 8, Part 4: LLM Cost, Scaling to 1,000 Users and Safe Deploys

**Watch:** [youtu.be/zrMGTiSirqA](https://youtu.be/zrMGTiSirqA) · **Code:** [`day08_production/`](../day08_production/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

How do you make an LLM app cheaper, faster, and ready for 1,000 users, and how do you change production without breaking it? The final part of Day 8.

## What you will learn

- Prompt caching, parallel tool calls, result caching and model routing, with the arithmetic
- Why cost per completed task beats cost per call
- Stateless replicas, connection pools, rate limits and availability maths
- Scaling to 1,000 concurrent users with Little's law
- A rollout checklist and an incident playbook for safe change

## Chapters

- [0:00](https://youtu.be/zrMGTiSirqA?t=0) Intro
- [0:22](https://youtu.be/zrMGTiSirqA?t=22) Latency and cost levers
- [2:56](https://youtu.be/zrMGTiSirqA?t=176) Reliability and scaling
- [6:21](https://youtu.be/zrMGTiSirqA?t=381) Changing production safely

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In the last part, we built an adapter that survives provider outages with retries, failover and circuit breakers. In this final part of Day 8, we make the chatbot cheaper and faster, scale it to a thousand users, and learn to change production safely.

## Latency and cost levers

Every lever in this section is judged by two numbers: how long the user waits, and how much each answered question costs.

First, a baseline with illustrative prices, chosen for easy maths. Each call sends four and a half thousand input tokens, two thousand of which are the fixed system prompt and tool descriptions, and gets three hundred tokens back. That is about one point eight cents per call, under two rupees. Small, but it multiplies fast.

**What one call costs (illustrative prices)**

1. Input: 4,500 tokens × $3 per million = $0.0135
2. Output: 300 tokens × $15 per million = $0.0045
3. Total: $0.018 per call, under two rupees

*Prices are made up for easy maths, not any provider's real rates.*

Lever one: prompt caching. The provider remembers the start of a prompt it has just seen, and charges much less, say a tenth, to reuse it. It only matches from the very beginning, so put stable content first, and the question last. Our cost drops from one point eight to one point two six cents. Thirty percent cheaper, and faster too. A timestamp at the top would ruin it.

**Put the stable part of the prompt first**

- No cache: $0.0180
- With cache: $0.0126

*30% cheaper, and the first word arrives sooner.*

Lever two: if the model asks for three independent tools, run them at the same time. You wait for the slowest, one point two seconds, not the sum of two point five. Lever three: cache tool results. Today's fund ranking does not change during the day, so keep it until the next data load. That is the time to live, or T T L.

**Parallel tools, and cache tool results**

- **Parallel tool calls**
  - Ranking 1.2 s, NAV 0.8 s, risk 0.5 s
  - One after another: 2.5 s
  - At the same time: 1.2 s
- **Cache with a TTL**
  - Today's ranking won't change today
  - Key on date, model and data version
  - Expire at the next data load

Lever four: model routing. Not every question needs the biggest model. A simple definition, like what is an expense ratio, can go to a small model costing a tiny fraction. If forty percent of questions are simple, cost per thousand questions falls from eighteen dollars to eleven forty. But only route if your Day 6 eval set proves quality holds.

**Cheap steps to a cheap model**

> Cost per 1,000 questions
- All on big model: $18.00
- 40% routed small: $11.40

*37% cheaper, only if your eval set says quality holds.*

Now the trap. Model B looks three times cheaper per call. But it needs more calls and succeeds only forty percent of the time, so users retry. Divide the cost by the tasks actually completed, and B is about twelve percent more expensive. Always measure cost per completed task, never per call.

**Cost per completed task, not per call**

| Model | Per call | Success | Per completed task |
|---|---|---|---|
| A | $0.018 × 2 calls | 90% | $0.040 |
| B (3× cheaper) | $0.006 × 3 calls | 40% | $0.045 |

*The cheap model is 12% more expensive per answer that works.*

## Reliability and scaling

Now, more users. What has to be true for our chatbot to grow from ten users to a thousand?

To serve more users, run more copies of the API and spread requests across them with a load balancer. This only works if each copy is stateless. If replica one held Priya's conversation in memory, her next message, landing on replica two, would find nothing. So memory lives in the database, keyed by thread id, and any copy can answer.

**More copies, behind a load balancer**

- Run more replicas of the API, spread requests across them
- Only works if replicas are stateless
- Conversation memory lives in Postgres, keyed by thread id
- Any replica can answer Priya's next message

Opening a database connection is slow, so each replica keeps a small pool of open ones to lend to requests. But Postgres allows about a hundred connections by default. Four replicas is fine. Scale to twelve with the same settings, and the database starts refusing connections. Scaling one layer can break the next.

**The database has a limit**

1. Postgres allows about 100 connections by default
2. 4 replicas × pool of 10, overflow 5 = up to 60: fine
3. 12 replicas, same settings = up to 180: refused

*Pool size × replicas must stay under the database limit.*

There are two kinds of rate limits. Your limits on users: requests per minute and tokens per day, so one heavy user or a script stuck in a loop cannot run up the bill. And the provider's limits on you. Go over them and you get a four two nine error, which our adapter handles by backing off and retrying.

**Two kinds, both matter**

- **Your limits on users**
  - Requests per minute per user
  - Token budget per day
  - Stops a looping script
- **Provider's limits on you**
  - Requests and tokens per minute
  - Exceed it: error 429
  - Adapter backs off and retries

Here is some availability arithmetic. A request passes through a chain: proxy, API, database, LLM. Multiply their availabilities, and the whole chain is only about ninety nine point two percent. Add an independent second provider, and both are rarely down at once, so the chain rises to about ninety nine point seven. That is the maths behind failover.

**A chain is weaker than its parts**

1. Proxy, API, database: 99.9% each; one LLM provider: 99.5%
2. Chain: multiply them = about 99.2%
3. Add an independent second provider: about 99.7%

A classic interview question: scale this to a thousand concurrent users. Do not start listing technologies. Start with arithmetic. Each user asks, reads for a minute, and asks again, and a request takes eight seconds. That is about fifteen requests per second. Little's law says requests in flight equals arrival rate times time, so about a hundred and twenty at any moment.

**Scale this to 1,000 concurrent users**

1. Each user: asks, reads ~60 s, asks again; a request takes 8 s
2. Arrival rate: 1,000 / 68 ≈ 15 requests per second
3. Little's law: in flight = rate × time ≈ 15 × 8 ≈ 120

*Start with arithmetic, not a list of technologies.*

Now walk the path. A few async replicas handle a hundred and twenty in-flight requests easily. The real bottleneck is the provider. About two LLM calls per request means nearly eight million input tokens a minute, likely above your account's limit. So caching and routing are not just cost tricks. They are scaling tools.

**The bottleneck is rarely the web server**

> **It is the provider's tokens-per-minute limit, and the bill.**
> ~29 LLM calls a second × 4,500 tokens ≈ 7.9 million input tokens a minute. Caching and routing are scaling tools.

Quick check. Pause and answer: why must replicas be stateless before you add more? The answer: the next message may land on a different copy. If memory lived inside one replica, the conversation would vanish. Keep it in the database.

**Quick check:** Why must API replicas be stateless before you can add more of them?

<details><summary>Answer</summary>

The next message may land on a different replica; memory must live in the database, not one copy.

</details>

## Changing production safely

Last topic, and maybe the most important. Most production incidents are not caused by traffic. They are caused by a change.

Imagine this. Your daily data job adds a few rows each night, and a downstream reader picks up new rows by their arrival time. One day you run a big one-off bulk load to fill history. It stamps the arrival time differently, and the reader quietly skips those rows. No error, no crash. Fund prices just go missing in the app.

**Imagine a bulk data load**

> **A one-off bulk load writes rows a downstream reader doesn't expect.**
> No error anywhere. The reader just quietly skips them, and fund prices go missing.

The answer is not to stop changing things. It is to make each change small, verified and reversible. Small, so you know what caused a problem. Verified by reading the real output, because no errors is not the same as correct. And with a rollback decided calmly in advance, not invented under pressure.

**Small, verified, reversible**

- Don't stop changing things: make each change small
- Verify the real output, not just “no errors”
- Decide the rollback before you start

Here is a rollout checklist you can reuse. Before: CI green, tested on dev with real questions, the full live configuration read, the rollback written down. During: the smallest reversible step, then one request that should work and one that should fail politely, like a Sunday date. After: watch errors, latency and token spend for an hour.

**Before, during, after**

| Phase | Do this | Why |
|---|---|---|
| Before | CI green; verified on dev with real questions | Catch bugs where users can't see |
| Before | Read the full live config; write the rollback | Surprises live in fields you didn't touch |
| During | Smallest reversible step; check right host | Small blast radius |
| During | One known-good and one known-bad request | Test happy and error paths |
| After | Watch errors, p95 latency, token spend for an hour | Some failures need real traffic |

And when something breaks anyway, follow the playbook. Detect it. Mitigate first: roll back, do not debug a live fire while users suffer. Communicate clearly. Then find the root cause and fix it properly. Finally, prevent it: in our bulk load example, a check that compares row counts before and after, so it can never fail silently again.

**The incident playbook**

1. Detect: alert, dashboard, or a user
2. Mitigate first: roll back to last known-good
3. Communicate: what broke, what you did, next update
4. Root-cause, then fix properly
5. Prevent: add a test or check; blameless write-up

Final check. Pause and answer: users report wrong numbers right after a deploy. What is your very first move? The answer: roll back to the last known-good version and tell users. Root cause comes second, once nobody is affected.

**Quick check:** Users report wrong numbers right after a deploy. What is your very first move?

<details><summary>Answer</summary>

Mitigate: roll back to the last known-good version, tell users, then find the root cause.

</details>

Let's recap Day 8's final part. Prompt caching, parallel tools, result caching and routing cut both cost and waiting. Judge cost per completed task. Stateless replicas, sensible pools and failover keep the system up. Scale with arithmetic first. And change things small, verified and reversible. Next, Day 9: putting all of this together in system design interviews.

- Caching, parallel tools, result cache and routing cut cost and wait
- Judge cost per completed task, not per call
- Stateless replicas, pools under the DB limit, failover for availability
- Scale with arithmetic: Little's law, then find the bottleneck
- Change small, verified, reversible; mitigate first

All the code for Day 8 is in the day eight production folder, linked in the description. If this helped, subscribe, and I will see you on Day 9.

---

← [Day 8, Part 3](day08_p3.md) · [All lessons](README.md) · [Day 9, Part 1](day09_p1.md) →
