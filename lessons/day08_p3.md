# Day 8, Part 3: LLM Retries, Failover and Circuit Breakers: Build a Resilient Adapter

**Watch:** [youtu.be/6-v_9HkONxM](https://youtu.be/6-v_9HkONxM) · **Code:** [`day08_production/`](../day08_production/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

What happens to your AI app when the LLM provider is slow, overloaded or down? In this episode we build a vendor-agnostic LLM adapter that keeps the research assistant chatbot answering.

## What you will learn

- Why every LLM call should go through one adapter, never a provider SDK directly
- Envelope normalisation: what really differs between providers
- Timeouts, retries with exponential backoff and jitter, and an overall deadline
- Failover to a second provider, and the circuit breaker pattern
- Graceful degradation: the numbers still arrive when the LLM is down
- Streaming answers with Server-Sent Events

## Chapters

- [0:00](https://youtu.be/6-v_9HkONxM?t=0) Intro
- [0:20](https://youtu.be/6-v_9HkONxM?t=20) Why one adapter for every LLM call
- [1:57](https://youtu.be/6-v_9HkONxM?t=117) Timeouts, retries and deadlines
- [3:49](https://youtu.be/6-v_9HkONxM?t=229) Failover and circuit breakers
- [6:11](https://youtu.be/6-v_9HkONxM?t=371) Graceful degradation and streaming

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In the last part, we added a safe front door, automatic checks, and proper secret handling. Now we tackle the question every production team faces: what happens when the LLM provider is slow, overloaded, or simply down?

## Why one adapter for every LLM call

Let's start with a design decision that makes everything else in this video possible: one adapter, through which every LLM call must pass.

Why an adapter? Providers change models and prices every few months. A client may insist on a particular provider. You may want cheap steps on a cheap model. Retries and logging must happen on every call, so they belong in one place. And for testing, the fake LLM from Day 3 plugs into the same shape, with no key and no cost.

**Five reasons to never call a provider directly**

- Providers change models, prices and APIs every few months
- Clients may require a specific provider or region
- Routing: cheap steps to cheap models
- Retries, timeouts, logging: in one place, never forgotten
- Testing: a fake LLM with the same shape costs nothing

Think of UPI. When you pay at a shop in Bengaluru, you use one app, and you do not care which bank sits on the other side. The adapter is the same idea. Your application speaks one simple language, and the adapter translates to whichever LLM provider is configured.

**Like UPI for language models**

> **Your app speaks one language. The adapter speaks to every provider.**
> You pay with UPI; you do not care which bank is on the other side.

The envelope is the wrapping around the content: where the system prompt goes, how tools are declared, how a tool call comes back. Every provider does it differently. A classic bug: one provider returns tool arguments as a dictionary, another as a text string. Code written for the first breaks on the second. The adapter converts everything into one internal shape, in exactly one file.

**What actually differs between providers**

| Thing | Why it bites |
|---|---|
| Where the system prompt goes | A separate field for one, a message for another |
| How tools are declared | Different JSON shapes |
| How a tool call comes back | Arguments as a dict, or as a JSON string |
| How token usage is reported | Different field names |

## Timeouts, retries and deadlines

Now, the reliability policy that lives inside the adapter, wrapped around every single call.

Rule one: always set a timeout, the maximum time to wait for one call. Without it, a single stuck connection can hang Priya's request forever and tie up a worker. Set it comfortably longer than a normal answer, but never infinite.

**Always set a timeout**

- Timeout: the longest you wait for one call
- Without it, a hung connection hangs the user forever
- Set it longer than a normal answer, never infinite

Rule two: when a call fails for a temporary reason, wait and try again, doubling the wait each time. Half a second, one second, two, four. This is called exponential backoff. Add a small random extra wait, called jitter, so a thousand clients that failed together do not all retry at the same instant, like the Tatkal rush at ten A M.

**Retry with exponential backoff**

> Wait before each retry (seconds)
- Retry 1: 0.5 s
- Retry 2: 1.0 s
- Retry 3: 2.0 s
- Retry 4: 4.0 s

*Plus a little random jitter, so failed clients don't retry in lockstep.*

Rule three: retry only errors that can recover. Timeouts, connection drops, four two nine meaning slow down, and five hundred style server errors are worth retrying. But a four hundred means our own request is broken, and a four oh one means the key is wrong. Retrying those just repeats the mistake and hides our bug.

**Retry only what can recover**

- **Retry**
  - Timeouts, connection errors
  - 429: rate limited
  - 5xx: server errors, overloaded
- **Never retry**
  - 400: our request is malformed
  - 401: bad key
  - Retrying hides our own bug

Rule four: add a deadline, a cap on the total time across all attempts. Look at this illustrative policy. Thirty second timeout, three attempts, short waits in between. The worst case is ninety one and a half seconds, and with failover, double that. No analyst waits three minutes. Cap the total.

**Add an overall deadline**

1. Timeout 30 s per attempt, 3 attempts
2. Waits between attempts: 0.5 s + 1 s
3. Worst case: 3 × 30 + 1.5 = 91.5 seconds
4. With failover to a second provider: double that

*Nobody waits three minutes. Cap the total time.*

## Failover and circuit breakers

Retries handle a hiccup. But what if the provider is properly down?

Failover means: if the primary provider keeps failing after its retries, try the next one in a configured list. That could be another provider, or another model. The user gets the same answer, just a little slower, and usually never knows anything went wrong.

**Try the next provider in the list**

**Primary** (529 overloaded, 3 times) → **Adapter** (fails over) → **Backup** (answers normally)

*The user gets the same answer, a bit slower.*

Without one more piece, every request still pays the full retry cost against a provider that is clearly dead. A circuit breaker fixes that, like the trip switch in your home. After several failures in a row, it opens, and calls go straight to the backup for a cool-down period. Then it lets one test call through. If that works, it closes again.

**Stop hammering a provider that is down**

1. Closed: calls flow normally
2. N failures in a row: open, skip it for a cool-down
3. Cool-down over: half-open, let one test call through
4. Test succeeds: closed again

Here is the heart of llm adapter dot py. The outer loop is failover across providers. The breaker check skips a dead one. The inner loop retries with exponential backoff and jitter, inside the deadline. Notice what is not caught: a fatal error, like a malformed request, goes straight up. Run python day08 production slash llm adapter dot py to see all three scenarios with fake providers.

**The resilient adapter, in short**

`day08_production/llm_adapter.py`
```python
class ResilientLLM:
    def complete(self, system, messages, tools) -> LLMResult:
        deadline = time.monotonic() + self.deadline_s
        for provider in self.providers:              # FAILOVER
            if self.breaker[provider.name].is_open():
                continue                             # skip a dead provider
            for attempt in range(self.attempts):     # RETRY
                try:
                    result = provider.complete(system, messages, tools)
                    self.breaker[provider.name].success()
                    return result
                except RetryableError:
                    self.breaker[provider.name].failure()
                    wait = 0.5 * 2 ** attempt + random.uniform(0, 0.5)
                    if time.monotonic() + wait > deadline:
                        raise LLMUnavailable("deadline")
                    time.sleep(wait)
        raise LLMUnavailable("all providers failed")
```

One question interviewers love: is your backup really independent? Two models at the same provider usually share the same servers, so they tend to fail together. Real redundancy means a different provider, or at least a different region. Always challenge the independence assumption.

**Is failover really independent?**

> **Two models at the same provider usually fail together.**
> Real redundancy needs failures that are independent: a different provider or region.

An adapter only works if nobody goes around it. A quick direct call to a provider library looks perfectly reasonable in review, and works fine, until the day the provider is down. That is why we ban those imports in the lint gate from the last part. Review might catch it. The lint rule guarantees it.

**Nobody may bypass the adapter**

> **The lint gate bans importing provider SDKs anywhere else.**
> Review might catch a direct call. The lint rule guarantees it.

## Graceful degradation and streaming

Now the worst day. Every LLM provider is down at once. Does our chatbot just show an error?

Not if we design it well. Remember the rule from Day 1: the model ranks, the LLM explains. The numbers come from our fund ranking tool, not the LLM. So if the LLM is unavailable, the app can still call rank funds and show the table with a short notice. Priya still gets Bharat Growth Fund at the top. Only the explanation is missing.

**The numbers still arrive**

`day08_production/app.py`
```python
try:
    answer = await agent.answer(req.thread_id, req.message)
except LLMUnavailable:
    table = rank_funds(as_of=parsed_date, top_n=5)   # the tool still works
    answer = format_table(table) + (
        "\n\nThe language model is temporarily unavailable; "
        "this is the raw ranking without commentary.")
```

Notice where this code lives: in the app, not the adapter. The adapter knows about providers, so it simply raises an error. The app knows about users, so it decides what they see. One honest caveat: the app must understand the question without the LLM, perhaps with a simple rule or a button. It is a design you build, not magic.

**Degradation lives in the app, not the adapter**

- The adapter knows providers: it raises LLMUnavailable
- The app knows users: it decides what they see
- Needs a way to understand the question without the LLM

Finally, streaming. An LLM writes one token at a time. Without streaming, the user stares at a spinner until the very last token. With streaming, each token goes to the browser as soon as it exists. The total time is the same, but the wait feels far shorter, because what users feel is the time to the first word.

**Same total time, much shorter wait**

- **No streaming**
  - Spinner for the whole answer
  - Then everything at once
- **Streaming**
  - First words in about a second
  - Text appears as it is written

The simplest way to stream to a browser is Server-Sent Events. The response stays open, and the server pushes small text messages, each with an event name and a data line. We send a status message while the tool runs, then one token message per word. And remember from the last part: turn Nginx buffering off, or all of this arrives at once.

**Streaming from FastAPI**

`day08_production/app.py`
```python
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def events():
        yield "event: status\ndata: ranking funds...\n\n"
        async for token in agent.stream(req.thread_id, req.message):
            yield f"event: token\ndata: {token}\n\n"
        yield "event: done\ndata: \n\n"
    return StreamingResponse(events(), media_type="text/event-stream")
```

Quick check. Pause and answer: the provider returns four hundred, bad request. Should the adapter retry, or fail over? The answer: neither. A four hundred means our own request is broken. Sending it again, anywhere, just repeats the bug and hides it. Raise the error so we fix it.

**Quick check:** The provider returns 400 Bad Request. Should the adapter retry, or fail over to the backup?

<details><summary>Answer</summary>

Neither. A 400 means our request is broken; retrying or failing over just repeats our own bug. Raise it.

</details>

Let's recap. Every LLM call goes through one adapter, and lint stops anyone bypassing it. The adapter normalises each provider into one shape. It uses timeouts, backoff with jitter, and a deadline, retrying only recoverable errors. Failover and a circuit breaker handle real outages. And graceful degradation keeps the numbers flowing. Next: cost, scaling to a thousand users, and changing production safely.

- Every LLM call goes through one adapter; lint bans bypasses
- Normalise each provider's envelope into one internal shape
- Timeout, backoff with jitter, retry only recoverable errors, deadline
- Failover plus circuit breaker; challenge independence
- Degrade gracefully: tool numbers survive; stream with SSE

The adapter code is in the day eight production folder, linked in the description. If this helped, subscribe, and I will see you in the next video.

---

← [Day 8, Part 2](day08_p2.md) · [All lessons](README.md) · [Day 8, Part 4](day08_p4.md) →
