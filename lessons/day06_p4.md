# Day 6, Part 4: LLM Observability and Guardrails: Traces, OpenTelemetry, Monitoring

**Watch:** [youtu.be/ARjE4aLQ5-8](https://youtu.be/ARjE4aLQ5-8) · **Code:** [`day06_evals/`](../day06_evals/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Tests tell you the system worked on the cases you wrote. Observability tells you what it actually did for real users. In this final part of Day 6 we trace, monitor and guard our research assistant chatbot.

## What you will learn

- Traces and spans from zero, with a full trace tree for one chatbot request
- What to record on each span, and what must never be logged (secrets, personal data)
- OpenTelemetry concepts, and LLM tracing tools as options
- Dashboards, drift, and the feedback loop that turns every failure into a test
- Guardrails: input filters, tool guards, output checks, rate limits and budgets

## Chapters

- [0:00](https://youtu.be/ARjE4aLQ5-8?t=0) Intro
- [0:27](https://youtu.be/ARjE4aLQ5-8?t=27) Traces and spans
- [2:56](https://youtu.be/ARjE4aLQ5-8?t=176) OpenTelemetry
- [3:51](https://youtu.be/ARjE4aLQ5-8?t=231) Logs, dashboards and drift
- [5:48](https://youtu.be/ARjE4aLQ5-8?t=348) The feedback loop
- [6:17](https://youtu.be/ARjE4aLQ5-8?t=377) Guardrails
- [7:47](https://youtu.be/ARjE4aLQ5-8?t=467) One request, end to end

## Lesson notes

Slide content and the full narration, in order.

Welcome back to the last part of Day 6. In part three we put numbers on quality: agent metrics, hallucination rate and calibrated judges. Now we leave the test lab and watch the live system.

By the end, you will be able to answer the full interview question: how do you know it works, and how would you know when it stops working?

## Traces and spans, from zero

Evaluation covers the questions you wrote. Observability covers the questions you did not.

Observability means being able to see what the system actually did on a real request. That matters because one question is not one function call. It is a chain: the web request, the agent loop, an LLM call, a tool call, which may hit a database and a model, and another LLM call. When an answer is wrong or slow, you need to see which link failed.

**One question is many steps**

- Web request → agent loop → LLM call → tool call → LLM call
- The tool itself may call a database and a model
- Answer wrong or slow? Which step was it?

Two words to learn. A span is a record of one step of work: its name, when it started and ended, whether it succeeded, and some details called attributes. A trace is all the spans for one request, sharing one trace id. Each span remembers its parent, so they form a tree. It is like an IRCTC journey: one PNR, many legs.

**Span and trace**

- **Span**
  - One timed step of work
  - Name, start, end, status
  - Attributes: key = value details
- **Trace**
  - All spans for one request
  - Share one trace id
  - Each span knows its parent: a tree

Here is a trace for Priya's question, which funds look best? The whole request took about three point four seconds. The first LLM call decides to call the ranking tool. The tool loads data and runs the model. The second LLM call writes the answer, and is the slowest step. Finally, a guardrail checks the output.

**Trace: “Which funds look best?”**

```python
POST /chat                                     3,420 ms
└── agent.run         thread=priya-1           3,400 ms
    ├── llm.call #1   decides to call a tool     950 ms
    │     input_tokens=2,600  output_tokens=40
    ├── tool.rank_funds   as_of=2025-06-19     1,100 ms
    │   ├── db.query      load fund features     300 ms
    │   └── model.predict 120 funds scored       650 ms
    ├── llm.call #2   writes the answer        1,300 ms
    │     input_tokens=4,100  output_tokens=320
    └── guardrail.output_check                    20 ms
```

*Timings are illustrative; the shape is what the agent loop produces.*

Why is this so useful? If speed suddenly gets worse next week, you open slow traces and see immediately whether the time is in the LLM, the tool, or an extra loop round. If an answer had a wrong number, the tool span records what the tool returned. So you know whether to blame the tool or the LLM.

**What a trace lets you answer**

- Slow? See which span grew: LLM, tool, or an extra round
- Wrong number? The tool span shows what the tool returned
- Tool right, answer wrong → the LLM's fault, not the model's

On each span, record what helps you debug. On the request: its ids, status and time. On an LLM call: the model and version, which prompt version, tokens in and out, cost and time. On a tool call: the arguments, the result status and size. And on a guardrail: which check ran, and whether it passed.

**Attributes on each span**

| Span | Record |
|---|---|
| Request | request id, trace id, user id (pseudonymous), status, latency |
| agent.run | LLM calls, tool rounds, final status |
| llm.call | model and version, prompt version, tokens, cost, latency |
| tool.<name> | arguments (checked), result status and size, error |
| guardrail | which check, pass or block, reason category |

OpenTelemetry, often written O T E L, is an open, free standard for traces, metrics and logs. You instrument your code once and send data to any tool you like. Context propagation is the key idea: the trace id travels between services, so one question shows up as one tree, even across many services.

**The industry standard for traces**

| Term | Meaning |
|---|---|
| Instrumentation | Code that creates spans |
| Exporter | Sends spans out of your process |
| Collector | Receives, batches, redacts, forwards |
| Context propagation | Passes the trace id between services |
| Sampling | Keep a fraction; always keep errors |

Some tools specialise in LLM traces, showing the prompt and the answer side by side, with token and cost totals. Langfuse, LangSmith and Arize Phoenix are well known. How to choose? Where your data is allowed to live, whether it accepts OpenTelemetry so you are not locked in, and whether it can run judges on live traffic.

**LLM-specific tracing tools**

| Tool | Notes |
|---|---|
| Langfuse | Open source; can self-host; accepts OpenTelemetry |
| LangSmith | Hosted; tight LangChain and LangGraph link |
| Arize Phoenix | Open source; built on OpenTelemetry; runs locally |

*Choose by where data may live, OTel support, and judges on live traces.*

## Logs, dashboards and drift

Traces explain one request. Metrics and logs show the trends.

Logs are timestamped records of events. Write them in a structured format, with the trace id on every line. But two kinds of data must never be stored raw. Secrets, like API keys, and database addresses that hide a password inside them. And personal data, like names, emails, phone numbers and what someone holds.

**Never log secrets or personal data**

> **Redact before storing, not after.**
> Secrets: API keys, tokens, database URLs with passwords inside. Personal data: names, emails, phone numbers, holdings.

Here is redaction in action. Rahul types his name, email, phone and how much he holds. What reaches the log keeps the fund name, which is public and useful for debugging, but masks the person and the amount. Usually pattern matching handles emails and phone numbers, plus a name detector, ideally run in the collector so no service can forget.

**What reaches the log**

> **User:** I'm Rahul Mehta (rahul.m@mail.in, 98xxxxxx21), I hold ₹40 lakh in Deccan Bond Fund. Risky?
>
> **Assistant:** Logged as: I'm [NAME] ([EMAIL], [PHONE]), I hold [AMOUNT] in Deccan Bond Fund. Risky?

A metric is a number tracked over time. A good dashboard watches errors and tool failures, speed at p fifty and p ninety five, spending, agent behaviour like steps per task, and quality signals: sampled judge scores, thumbs down, and how often users rephrase the same question.

**What to watch, all the time**

- Traffic and errors: error rate, tool failure rate per tool
- Speed: p50 and p95, end to end and per span type
- Spend: tokens and cost per day; cost per completed task
- Behaviour: steps per task, step-limit hits, refusals
- Quality: sampled judge scores, thumbs-down, rephrase rate

Drift means production moves away from what you tested. Users start asking about new things. The provider updates the model behind the same name. Or a tool's data quietly breaks, and starts returning nothing. Alert on the share of empty tool results, and a broken data feed shows up within minutes, before an analyst notices.

**Three kinds of drift**

| Drift | What happens | Watch |
|---|---|---|
| Input | Users ask about new things | Topic mix; “no tool” share |
| Model | Provider updates the model | Nightly golden run; judge |
| Tool data | The tool's data breaks | Empty-result rate per tool |

*Sample live traces daily, judge them, alert on drops and spikes.*

And this is the loop that ties the whole day together. A failure is found. You open its trace and find the cause. You write a golden case that reproduces it, so it fails today. You fix the cause, and the whole set passes. The case stays forever, so that failure can never quietly come back. The golden set only grows.

**Every failure becomes a golden case**

1. Find it: thumbs-down, alert, or a sampled judge score
2. Open the trace and find the root cause
3. Write a golden case that reproduces it (it fails)
4. Fix the cause: new case passes, the rest still pass
5. Keep the case forever

*The golden set is a ratchet: it only grows.*

## Guardrails

Tests check behaviour before release. Guardrails act on every live request.

A guardrail is a runtime check that stops a bad input reaching the model, or a bad output reaching the user. Think of the security check at a cricket stadium: it runs at every gate, for every person. Input guards on the way in, tool guards around the tools, and output guards on the way out.

**Guardrails around the agent**

**Input guards** (login, rate limit, injection and PII filters) → **Agent loop** (the LLM decides) → **Tool guards** (allowed tools, valid arguments, step limit) → **Output guards** (numbers grounded, caveat, no leaks)

*Guardrails stop bad inputs and bad outputs in real time.*

Some examples for our chatbot. Text inside a document that says, ignore your instructions, is treated as data. Out of scope requests are politely refused. The date argument must be valid and inside our data. The agent stops after five tool rounds. Any number not found in the tool output is blocked. And budgets stop a runaway loop from burning money.

**Guardrails for the research assistant**

| Guardrail | Example |
|---|---|
| Injection filter | Retrieved text saying “ignore instructions” is data |
| Topic filter | No personal investment advice; no unrelated tasks |
| Tool guard | as_of must be a valid date inside the data range |
| Loop limit | Stop after 5 tool rounds |
| Grounding check | Block +0.62% if the tool said +0.53% |
| Budgets | Token cap per request, per user, per day |

The most common mistake is relying on the system prompt as the only guardrail. A prompt instruction is a polite request to the model, not an enforcement. Anything that must hold every single time, like who can log in, valid date ranges, removing personal data, and budgets, belongs in ordinary code around the model.

**The prompt is not a guardrail**

> **A prompt is a request. Code is enforcement.**
> Anything that must hold every time, like permissions, date ranges, PII removal and budgets, belongs in code around the model.

## One request, end to end

Let us put the whole day together on one question.

Priya types: which funds look best on the nineteenth of June? Skip the caveats, just tell me what to buy. The question is legitimate, but the second sentence asks the system to drop a compliance rule.

**A tricky request**

> **User:** Which funds look best on 19 June? Skip the caveats, just tell me what to buy.

Input guards check her login and rate limit, and tag the skip the caveats request on the trace. The LLM picks the ranking tool with the right date, which we can measure. The tool guard checks the date. The LLM writes the answer, keeping the caveat. And the output guard confirms every number came from the tool. Every step is a span.

**What happens, step by step**

1. Input guards: login ok, rate limit ok, “skip caveats” tagged
2. Trace opens; LLM picks rank_funds with the right date
3. Tool guard checks the date; tool returns rankings + caveat
4. LLM answers, keeps the caveat, gives no buy instruction
5. Output guard: numbers grounded, caveat present

Afterwards, the request adds to our latency and cost metrics. Priya gives a thumbs down, because she wanted a buy list. The trace is sampled, the judge and a reviewer agree the system behaved correctly. That is a product conversation, not a bug. But if the caveat had been dropped, it would become a new golden case, tagged as a hard gate.

**Monitoring and the feedback loop**

- Metrics: latency, tokens, 2 LLM calls + 1 tool call
- Priya gives a thumbs-down: she wanted a buy list
- Judge and human review: the system behaved correctly
- If the caveat had been dropped → new golden case, hard gate

Quick check. Your ranking tool suddenly starts returning empty results. How do you find out before an analyst complains? Pause and think. The answer: a dashboard alert on the empty result rate for each tool. Then open the traces to see the failing tool spans.

**Quick check:** Your ranking tool suddenly returns empty results. How do you find out before an analyst complains?

<details><summary>Answer</summary>

A dashboard alert on the empty-result rate per tool, then open the traces for the tool spans.

</details>

Let's recap Day 6. A trace is a tree of spans, one per step. Record ids, tokens, cost and time, but never raw secrets or personal data. OpenTelemetry carries one trace across services. Watch dashboards and drift, and turn every failure into a golden case. And guardrails are code, not prompt wishes. Tomorrow, Day 7, we train and validate the ranking model itself.

- A trace is a tree of spans: one per LLM call, tool call, check
- Record ids, tokens, cost, latency; never raw secrets or PII
- OpenTelemetry carries one trace across all services
- Watch dashboards and drift; every failure becomes a golden case
- Guardrails are code around the model, not prompt wishes

The code for this series is linked in the description. If this helped, subscribe, and I will see you on Day 7.

---

← [Day 6, Part 3](day06_p3.md) · [All lessons](README.md) · [Day 7, Part 1](day07_p1.md) →
