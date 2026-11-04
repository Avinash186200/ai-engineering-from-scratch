# Day 2, Part 2: Zero-Shot, Few-Shot, Chain of Thought and Prompt Caching

**Watch:** [youtu.be/1Be6blFvHjE](https://youtu.be/1Be6blFvHjE) · **Code:** [`day02_prompting/`](../day02_prompting/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

The standard prompting techniques every AI engineer must know, explained with plain examples, plus prompt caching: the trick that can cut your input bill by about 80 percent.

## What you will learn

- Zero-shot prompting, and why being specific beats being clever
- Few-shot prompting (in-context learning) and how to pick examples
- Chain of thought, and when to use a tool instead
- Decomposition: several small model calls instead of one giant prompt
- Built-in thinking and effort settings
- Prompt caching: the prefix rule, what to put first, and the cost arithmetic

## Chapters

- [0:00](https://youtu.be/1Be6blFvHjE?t=0) Intro
- [0:26](https://youtu.be/1Be6blFvHjE?t=26) Zero-shot: just ask, specifically
- [0:29](https://youtu.be/1Be6blFvHjE?t=29) Zero-shot
- [1:31](https://youtu.be/1Be6blFvHjE?t=91) Few-shot: show, don't tell
- [1:34](https://youtu.be/1Be6blFvHjE?t=94) Few-shot
- [3:16](https://youtu.be/1Be6blFvHjE?t=196) Chain of thought and decomposition
- [3:19](https://youtu.be/1Be6blFvHjE?t=199) Chain of thought
- [4:11](https://youtu.be/1Be6blFvHjE?t=251) Decomposition
- [4:41](https://youtu.be/1Be6blFvHjE?t=281) Thinking and effort
- [5:31](https://youtu.be/1Be6blFvHjE?t=331) Prompt caching
- [5:37](https://youtu.be/1Be6blFvHjE?t=337) Prompt caching

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In the last part, we learned the four message roles and the seven parts of a system prompt. Now we learn the techniques for getting better answers, and a trick for making every call much cheaper.

These four techniques are the standard vocabulary. You will hear them in every AI engineering interview.

## Zero-shot: just ask, specifically

First, zero shot.

Zero shot means you give the model an instruction with no examples at all. It relies only on what it learned in training. It is the cheapest kind of prompt, so it is always where you start.

**An instruction, no examples**

> **Zero-shot = an instruction with no examples.**
> Cheapest prompt. Always the starting point.

Here is a vague zero shot prompt: summarise this fund factsheet. You get a fluent paragraph, but its length changes every time, and it may mix the factsheet with general background, sometimes even numbers that are not in the document.

Now the specific version. Summarise it in three bullets: the main view, the funds it names, and the reason. Use only facts in the document. And if it names no funds, say so. Same technique, zero shot, but now the shape is consistent and the edge case is handled. The fix was being specific.

**Specific beats clever**

- **Before**
  - "Summarise this fund factsheet."
  - Random length
  - Mixes facts with general background
- **After**
  - Three bullets: main view, funds named, reason
  - Use only facts in the document
  - If no funds are named, say so

*The fix was specificity, not a clever trick.*

## Few-shot: show, don't tell

Second, few shot.

Few shot means putting two or three worked examples, question and ideal answer, inside the prompt. The model spots the pattern and follows it. Nothing is retrained. It is like showing a new cashier three filled-in receipts instead of reading out the rules.

**Learning from examples in the prompt**

> **Put 2 or 3 worked examples inside the prompt.**
> The model copies the pattern. No retraining: called in-context learning.

Here is a real problem. Rahul asks, is Deccan Bond Fund cheap? Sometimes the model treats cheap as a word to define and calls the definitions tool. Sometimes it calls the ranking tool. Inconsistent.

**The routing problem**

- Rahul asks: "Is Deccan Bond Fund cheap?"
- Sometimes the model calls lookup_definition ("cheap" is a word?)
- Sometimes it calls rank_funds (a judgement about a fund)

The fix is three short examples. A judgement about a fund goes to the ranking tool. A meaning of a word goes to definitions. A question about the model itself goes to model info. The boundary is shown, not described, and routing becomes consistent.

**Three examples at the boundary**

`added to system_prompt.md`
```python
Examples:
Q: Is Nifty Value Fund attractive today?
   -> call rank_funds        (a judgement about a fund)
Q: What does "expense ratio" mean?
   -> call lookup_definition (a definition question)
Q: How many features does the ranking model use?
   -> call model_info        (a question about the model)
```

A few rules. Choose the tricky boundary cases, not the easy ones. Vary them, because if every example uses the same date, the model may start using that date. And keep them short, because examples are paid for on every call.

**Choosing good examples**

- Cover the tricky boundary cases, not the easy ones
- Vary them: same date everywhere and the model copies the date
- Keep them short: examples cost tokens on every call

*Few-shot fixes inconsistent format and inconsistent choices.*

If you have done some machine learning, few shot is like adding a few labelled points right next to the decision boundary, except nothing is refitted. And the same risk applies as with any tiny training set: the model can latch onto an accidental feature.

**Few-shot as labelled points**

> **Like adding labelled points next to the decision boundary.**
> But nothing is refitted. And a tiny set has the usual risk: it can latch onto an accidental feature.

## Chain of thought and decomposition

Third, chain of thought.

Chain of thought means asking the model to write its reasoning before the answer. Remember, it writes one token at a time and cannot go back. Writing the steps first is like doing rough work in the margin of an exam paper. Each later word can lean on it.

**Reason first, answer last**

> **Ask the model to write its steps before the final answer.**
> It writes one token at a time and can't go back, so the steps give it room to work.

Example. How many of the top ten funds are equity funds, and what share is that? Asked directly, the model may glance and guess. Asked to list each fund with its category, count, divide, then answer, it becomes checkable. But even better: do the counting in code. Counting is deterministic work, and an LLM is not a calculator.

**How many of the top 10 are equity funds?**

1. List each fund in the tool result with its category
2. Count the equity funds
3. Divide by the number of funds shown
4. Give the answer in one sentence

*Better still: do the counting in code. An LLM is not a calculator.*

Decomposition goes further. Say Priya asks whether a forty page research note agrees with our model. Do not send it all in one giant prompt. Call one extracts each fund view as data. Code validates it and calls the ranking tool. Code compares the two. Call two explains. Each step can be tested on its own.

**Several small calls, code in between**

**Call 1** (extract fund views as JSON) → **Code** (validate, call rank_funds) → **Code** (join and compare) → **Call 2** (explain in 3 bullets)

*Each step has one job and can be tested on its own.*

Today's frontier models were trained to reason internally. Instead of writing think step by step, you switch thinking on and set an effort level: low, medium or high. Remember, thinking tokens are billed as output tokens. Use low effort for simple routing, more for multi step analysis, and choose by measuring on your test set.

**Modern models can think on their own**

| Control | What it does |
|---|---|
| Thinking mode | Model reasons privately before it answers |
| Effort level | low / medium / high: depth vs cost and wait time |
| Billing | Thinking tokens are billed as output, even if hidden |

*Low effort for routing; more for multi-step analysis. Measure, don't guess.*

Quick check. The chatbot formats its answers differently every time. Which technique do you try first? Pause now. The answer: few shot. Inconsistent format and inconsistent choices are exactly what two or three good examples fix.

**Quick check:** Your chatbot formats answers differently every time. Which technique do you try first?
- Chain of thought
- Few-shot examples
- Higher effort

<details><summary>Answer</summary>

Few-shot. Inconsistent format or choices is exactly what 2-3 examples fix.

</details>

## Prompt caching

Now, prompt caching. This one saves real money.

Remember, the API is stateless. Every call resends the tools, the system prompt and any reference documents. That fixed part is often thousands of tokens, identical every time. Processing it from scratch on every call wastes money and time.

**The same thousands of tokens, every call**

- Stateless API: every call resends tools, system prompt, documents
- That fixed part is often thousands of tokens
- Processing it from scratch each time wastes money and time

Caching lets the provider keep its processed version of the start of your prompt for a few minutes. If your next request starts exactly the same way, it reuses that work. On Anthropic, reading from cache costs about a tenth of a normal input token. Writing to cache costs a little more, about one and a quarter times.

**Reuse work on an identical start**

> **If the prompt starts exactly the same, the provider reuses its earlier work.**
> Reading from cache costs about a tenth of normal input, and answers start sooner.

The rule is an exact prefix match: the start must be identical, character for character. Change one character, and everything after it misses the cache. So order your prompt: tools first, then the system prompt, then fixed documents, then history, and the new question last. Stable first, changing last.

**Stable first, changing last**

**Tools** (never change) → **System prompt** (never changes) → **History** (grows) → **New question** (changes every time)

*One changed character breaks the cache from that point on.*

Watch out for silent cache killers. A system prompt that starts with the current time and the user's name changes on every request, so nothing is ever cached. Move the date into the latest user message. Also keep tool order fixed and JSON keys sorted. Then the prefix is the same for every user.

**One timestamp ruins everything**

- **Before**
  - System prompt starts: "Time: 14:32:07. User: Priya"
  - Changes every request
  - Nothing is ever cached
- **After**
  - Rules and tools first, never change
  - Date goes in the latest user turn
  - Same prefix for every user: cached

Some illustrative arithmetic. Six thousand stable tokens, five hundred changing tokens, a thousand requests a day, at three dollars per million input tokens. Without caching, nineteen dollars fifty a day. With caching, about three dollars thirty two. Roughly eighty three percent cheaper, just by ordering the prompt well.

**Daily input cost, 1,000 requests**

- No caching: $19.50
- With caching: $3.32

*6,000 stable tokens + 500 changing, $3 per million: about 83% cheaper.*

Three details. Very short prefixes are not cached at all; there is a minimum length, around a thousand tokens. Caches expire after a few idle minutes. And always confirm in the usage numbers each response returns, because a single timestamp can quietly drop your saving to zero.

**Three practical details**

- Short prompts aren't cached: there's a minimum, around a thousand tokens
- Caches expire after a few idle minutes (5 by default on Anthropic)
- Check the usage numbers in each response to confirm cache hits

If you have built data pipelines before, caching is just memoisation, or a feature store. Expensive work on inputs that do not change is computed once and reused. The prefix is the cache key. Change one raw input, and every value derived after it has to be recomputed. Same rule here.

**Caching is memoisation**

> **Like a feature store: compute once, reuse many times.**
> The prefix is the cache key. Change any upstream input and everything after it must be recomputed.

Quick check. If the model needs today's date, where does it go: the top of the system prompt, or the latest user message? The answer: the latest user message. Anything that changes must come after the stable part, or the cache never hits.

**Quick check:** Where should today's date go if the model needs it: top of the system prompt, or the latest user message?

<details><summary>Answer</summary>

The latest user message. Anything that changes must come after the stable, cached part.

</details>

Let's recap. Start with zero shot, and be specific. Few shot fixes inconsistent formats and choices. Chain of thought helps multi step reasoning, but arithmetic belongs in code. Decompose big tasks into small, testable calls. And for caching, put stable content first and changing content last. Next: structured output, getting JSON your code can actually trust.

- Zero-shot first, and be specific
- Few-shot fixes inconsistent format and choices
- Chain of thought for multi-step reasoning; arithmetic goes in code
- Decompose big tasks into small, testable calls
- Caching: stable content first, changing content last

The prompt file with the few shot examples is in the day two folder, linked in the description. Subscribe, and see you in the next part.

---

← [Day 2, Part 1](day02_p1.md) · [All lessons](README.md) · [Day 2, Part 3](day02_p3.md) →
