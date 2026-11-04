# Day 9, Part 3: System Design: AI Chatbot with Tools + Multi-Tenant Agent Platform

**Watch:** [youtu.be/R8mgn9dK5go](https://youtu.be/R8mgn9dK5go) · **Code:** [`day09_design/`](../day09_design/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Two more worked system design answers. First, a research assistant chatbot that answers with live model outputs, where the hard part is trust. Second, a multi-tenant agent platform serving 200 business customers, where the hard part is isolation and cost.

## What you will learn

- Why load is not the problem for an analyst chatbot, and what is
- Tool contracts: typed inputs, structured outputs, explicit errors, read-only
- Parity tests, checkpointed conversation state, and the "numbers only from tools" check
- Silo, pool and bridge isolation, row-level security, and leakage tests
- Rate limits, fair queueing, tool credentials, and model routing that cuts cost ~64%

## Chapters

- [0:00](https://youtu.be/R8mgn9dK5go?t=0) Intro
- [0:17](https://youtu.be/R8mgn9dK5go?t=17) The research assistant chatbot
- [4:36](https://youtu.be/R8mgn9dK5go?t=276) A multi-tenant agent platform

## Lesson notes

Slide content and the full narration, in order.

Welcome back. Last time we designed document question and answer for ten thousand employees, where the hard part was retrieval and permissions. Today, two designs where the hard part is different.

## The research assistant chatbot

Design B is our own project from this series: the research assistant chatbot.

The prompt: design a copilot that answers fund research questions using live outputs from our quantitative models. If you have built something like this, it is a big advantage. Just keep one rule: say we built, only for what really exists, and I would add, for everything else.

**What the interviewer says**

> **“Design a copilot that answers fund research questions using live outputs from our models.”**
> If you built something similar: “we built” for facts, “I would add” for the rest.

Clarify. About fifty analysts. They live in Excel and Jupyter, not only a chat window. Can the system trade? No, it is read only, people decide. Ten seconds is fine, because being right matters far more than being fast. And the data is confidential.

**I ask, and I assume**

| I ask | Assumed answer |
|---|---|
| Users? | About 50 analysts and fund managers |
| Where do they work? | A chat window, plus Excel and Jupyter all day |
| Can it act, e.g. trade? | No. Read-only. People decide |
| Latency? | 10 seconds is fine; correctness matters more |
| Sensitivity? | High: restricted, audited access |

Estimates. Fifty people, twenty questions each, is a thousand a day: tiny. Each answer needs two LLM calls, one to choose the tool and one to explain, about two point six cents. The ranking model itself runs in milliseconds. So I tell the interviewer: load is not the problem. Trust is. That is where my deep dive goes.

**One number decides the deep dive**

| Quantity | Arithmetic |
|---|---|
| Traffic | 50 × 20 = 1,000 questions a day ≈ 0.035 per second |
| LLM calls | 2 per answer: pick the tool, then explain |
| Cost | ≈ 2.6 cents a question ≈ $26 a day |
| Model compute | Ranking a few hundred funds: milliseconds |

*Load is not the problem. Trust is.*

The agent is a LangGraph graph from day three. The models sit behind M C P servers from day four, so the chatbot, Excel and Jupyter all call exactly the same tools. Excel cannot speak M C P, so a small gateway exposes the same tools as normal web A P Is. The LLM sits behind an adapter, so changing provider is a config change.

**One set of tools, three front doors**

**Chat · Excel · Jupyter** (three ways in) → **Agent** (LangGraph; routes each question) → **MCP tools** (fund-ranking model, read-only) → **LLM adapter** (swap providers by config)

*Plus: research retrieval · Postgres checkpoints · traces*

The deep dive starts with the tool contract. Inputs are narrow and typed: a date and a number, no free text. Output is structured, with the date, the ranking, which funds were excluded, and a caveat. Errors are explicit: not a business day comes back as a clear error the agent can explain, instead of a crash that turns into a guess. And it is read only.

**What a good tool contract looks like**

`day04_mcp/fund_mcp_server.py`
```python
@mcp.tool()
def rank_funds(as_of: date, top_n: int = 5) -> dict:
    """Rank funds by predicted 1-month return on a business day.
    Read-only. Numbers come from the ranking model."""
    if not is_business_day(as_of):
        return {"error": "no_data", "reason": "not a business day"}
    result = fund_model.rank_funds(as_of, top_n)
    return {"as_of": str(as_of), "ranked": result["ranked"],
            "excluded": result["excluded"],
            "caveat": "research signal, not advice"}
```

*Typed inputs · structured output · explicit errors · read-only*

Grounding means the answer must come from real sources. Three layers. First, architecture: the LLM never computes a number, it only copies one. Second, the prompt forbids any number not in a tool result. Third, a check in code: pull every number out of the answer, and confirm it appears in the tool output. If not, regenerate or refuse.

**Numbers only from tools, three layers**

1. Architecture: the LLM never computes a number; it copies from tool output
2. Prompt: never state a number that is not in a tool result
3. Code check: every number in the answer must appear in this turn's tool output

Two more things. Parity: wrapping a model in a tool can quietly change it, through a different date rule or a default setting. So freeze some inputs, and test in C I that the tool gives exactly the same answers as the original model. And state: save each conversation to Postgres, so a follow up like, and the second fund, still works after a restart.

**Two more things that build trust**

- Parity: model via tool = model run directly, on frozen inputs
- Exact match for ranks, tiny tolerance for decimals; runs in CI
- State: checkpoint each conversation to Postgres by thread id
- So “and the second fund?” works, and every step is auditable

And one design requirement people forget. The chatbot explains model outputs, so it must also explain how reliable they are. If the model's validation was weak, or close to what luck would give, say so, and make that caveat travel with every answer, not sit in a footnote.

**Explain how much to trust the numbers**

> **A system that explains numbers fluently is dangerous if it hides how reliable they are.**
> If the model's test results are weak or close to luck, say so, and attach that caveat to every answer.

A common probe: why M C P, and not just function calling? Answer: function calling is how the model asks for a tool. M C P is how the tool is served. Serving it once means every front door shares one implementation. And if the LLM provider goes down? Excel and Jupyter keep working, because they call the tools directly.

**Why MCP, not just function calling?**

> **User:** Why MCP and not just function calling?
>
> **Assistant:** Function calling is how the model asks for a tool. MCP is how the tool is served. Serving it once means the agent, Excel and Jupyter share one implementation, which is what parity needs.

## A multi-tenant agent platform

Design C often arrives as a follow up: now make it multi tenant.

A tenant is one customer company. Multi tenant means many companies share one platform, like flats in one apartment building: shared lifts and water, but nobody walks into another flat. Assume two hundred tenants, each building agents over their own documents and tools, and some tools can write, like creating a ticket.

**Agents as a product, for many companies**

- A tenant = one customer organisation
- Many tenants share one platform, but can never see each other
- Assume: 200 tenants, 10 to 2,000 users each; some tools can write

Estimates. Four lakh agent runs a day, four LLM calls each, is one point six million calls. About ninety three a second at peak. By Little's law, about four hundred sixty runs in flight, so we need a queue and workers, not one thread per request. One large model costs about twenty one thousand dollars a day. Send seventy percent of simple calls to a small model, and it drops by about sixty four percent.

**Cost is the business problem**

| Quantity | Arithmetic |
|---|---|
| Runs | 200 × 2,000 = 400,000 a day; × 4 LLM calls = 1.6 M calls |
| Rate | 1.6 M ÷ 86,400 ≈ 18.5/s; peak × 5 ≈ 93/s |
| In flight | 23 runs/s at peak × 20 s ≈ 460 runs |
| One big model | ≈ $21,600 a day |
| 70% to a small model | ≈ $7,740 a day: about 64% less |

The deep dive is isolation. Silo gives each tenant its own copy of everything: safest, most expensive. Pool shares everything and filters by tenant id: cheapest, but one missing filter is a leak. Bridge shares compute but separates the data. I would choose bridge, with a silo option for regulated customers like banks.

**Three isolation models**

| Model | Meaning | Trade-off |
|---|---|---|
| Silo | Each tenant gets its own stack | Safest; most expensive |
| Pool | Everything shared; filter by tenant id | Cheapest; one bug from a leak |
| Bridge | Shared compute, separate data stores | The usual middle |

*My choice: bridge, with a silo option for regulated tenants.*

Then make the tenant id impossible to forget. Row level security, so the database itself refuses another tenant's rows. A separate search index per tenant. A tenant context that every data function needs, so forgetting it will not compile. And a test in C I: put a secret string in tenant A, and check it never appears anywhere for tenant B.

**Make the tenant id impossible to forget**

- Postgres row-level security: the database refuses other tenants' rows
- One retrieval index per tenant: a search cannot reach other vectors
- A tenant context object every data function requires
- CI leakage test: a secret in tenant A must never appear for tenant B

Next, fairness. A noisy neighbour is one tenant whose bulk job slows everyone else. Defences: a rate limit per tenant, a daily token budget with alerts, and fair queueing, where workers serve tenants in turn, like a UPI server taking one request from each bank in rotation. A tenant that submits ten thousand runs waits behind its own runs, not everyone else's.

**The noisy neighbour problem**

- Token-bucket rate limit per tenant, e.g. 60 requests a minute
- Daily token budget: alert at 80%, stop or bill at 100%
- Fair queueing: workers take tenants in turn
- So a 10,000-run bulk job waits behind its own runs

Tools are where damage happens. Each agent has an allow list. A tenant's passwords live in a vault, and are added when the tool runs, so the LLM never sees them. Write tools need a policy or a human to click approve, because a wrong write costs far more than a click. And every tool call runs in a sandbox with a timeout.

**Where agents touch the outside world**

- Allow-list of tools per agent
- Tenant credentials in a vault, injected at call time; the LLM never sees them
- Write tools need policy approval or a human click
- Sandbox with timeouts for every tool call

The close. Version one: shared compute, row level security, an index per tenant, read only tools, per tenant limits, usage reports, and the leakage tests. Then write tools with approval, customers bringing their own model keys, routing by tier, and regional deployments, in the order customers ask for them.

**Ship the safe core first**

> **v1: pooled compute, row-level security, index per tenant, read-only tools, quotas, leakage tests.**
> Next: write tools with approval, bring-your-own keys, tier routing, regional stacks, silo option.

Quick check. Pause and answer: one tenant's usage suddenly jumps fifty times. What happens? The answer: their rate limit kicks in, fair queueing keeps everyone else moving, and their budget alert fires. Nobody else notices. If the demand is real, you raise their quota.

**Quick check:** One tenant's usage spikes 50 times. What happens on a well-designed platform?

<details><summary>Answer</summary>

Their token bucket empties and they get rate-limit responses; fair queueing keeps other tenants moving; a budget alert fires. Nobody else notices.

</details>

Let's recap. For the chatbot, estimates show load is tiny, so the deep dive is trust: tight tool contracts, numbers only from tools, parity tests and saved state. For the multi tenant platform, isolation in the database and the index, fairness with limits and fair queueing, and credentials the LLM never sees. Next video: the behavioural round, and the STAR method.

- Chatbot: load is tiny, so the deep dive is trust
- Typed, read-only tool contracts; numbers only from tools, checked in code
- Parity tests and checkpointed state make it auditable
- Multi-tenant: bridge model, row-level security, index per tenant
- Rate limits, fair queueing, vaulted credentials, routing by task

The tool server from day four is in the repo, linked in the description. Subscribe, and I will see you in the next video.

---

← [Day 9, Part 2](day09_p2.md) · [All lessons](README.md) · [Day 9, Part 4](day09_p4.md) →
