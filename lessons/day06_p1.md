# Day 6, Part 1: How to Test an AI Chatbot: Why LLM Evals Are Different

**Watch:** [youtu.be/AoVXsrUu-tg](https://youtu.be/AoVXsrUu-tg) · **Code:** [`day06_evals/`](../day06_evals/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

How do you know your AI chatbot actually works, and how would you know when it stops working? In this episode we start Day 6: testing and monitoring AI systems.

## What you will learn

- Why normal accuracy numbers do not work for free-text answers
- Six ways an LLM product breaks the old testing rules
- The eval pyramid: deterministic checks, LLM-as-judge, human review, online signals
- What each layer catches, what it costs, and which to build first
- Why one fluent answer can fail five separate checks

## Chapters

- [0:00](https://youtu.be/AoVXsrUu-tg?t=0) Intro
- [0:27](https://youtu.be/AoVXsrUu-tg?t=27) Where we are in the series
- [1:34](https://youtu.be/AoVXsrUu-tg?t=94) Why testing AI is different
- [5:03](https://youtu.be/AoVXsrUu-tg?t=303) Two answers, five checks
- [6:18](https://youtu.be/AoVXsrUu-tg?t=378) The eval pyramid

## Lesson notes

Slide content and the full narration, in order.

Hi, I'm Avinash, and welcome to Day 6 of AI Engineering from Scratch. Today is about one question: how do you know your AI system works, and how would you know when it stops working?

As always, no machine learning background is needed. And if the pace feels slow, watch at one point two five times speed.

Here is where we are. We have built a chatbot that uses tools, talks through MCP, and reads our own documents. Before we take it to production, we need to test it and watch it. That is today.

This question comes up in almost every AI engineering interview. People who have only built demos answer with adjectives: it works well, it is pretty accurate. People who have run a product answer with things: a test set, a gate, a trace and a dashboard. By the end of today, you will give the second kind of answer.

**Demo builders vs product builders**

> **“How do you know it works?”**
> Demo answer: adjectives. Product answer: a test set, a gate, a trace and a dashboard.

Today has four parts. First, why testing AI is different, and the four layers of testing. Second, building a test set and a gate. Third, measuring quality with numbers. And fourth, watching the live system and putting guardrails around it.

**The plan for Day 6**

- Part 1: why testing AI is different, and the eval pyramid
- Part 2: golden sets, the eval harness and the deploy gate
- Part 3: measuring agents, hallucination and LLM judges
- Part 4: traces, monitoring and guardrails

## Normal testing, and why it breaks

Let us start with how testing usually works, and why it breaks for a language model.

Think about testing a normal program. A function that adds two numbers must return five for two plus three. There is one right answer, and it gives the same output every single time. A test is just: does the output equal the expected value?

Now our research assistant chatbot. Priya asks, which funds look best this week? There are many correct answers, written in many different ways. And the same question can give a slightly different answer each time. You cannot simply check that a paragraph equals an expected paragraph.

**Testing a normal program**

- **A normal program**
  - add(2, 3) must return 5
  - One right answer
  - Same input, same output, every time
- **Our chatbot**
  - “Which funds look best?”
  - Many right answers, in any wording
  - Same question, different answers

*You cannot check “output == expected” on a paragraph.*

A short note if you have done some machine learning. There, every row has a label, and one number, like accuracy, sums up quality. The model is fixed once trained. With an LLM product, every one of those assumptions breaks. If you have not done machine learning, that is fine, the next slides explain it plainly.

**What a metric used to look like**

| Classic machine learning | An LLM product |
|---|---|
| One label per row | Many acceptable answers |
| One number: accuracy, error | Many qualities at once |
| Model fixed after training | Changes with every prompt edit |

Here are six reasons, one at a time. First, the output is free text. Bharat Growth Fund ranks first, and the top fund is Bharat Growth, say the same thing in different words.

Second, quality has many sides at once. An answer can be correct but slow, fast but too expensive, or excellent but unsafe. One score would hide which one went wrong.

Third, there is rarely a single true answer. For, explain why this fund ranks first, there are many good explanations and many bad ones. So the expected result is a description of good behaviour, not one fixed value.

Fourth, the thing you are testing is the whole system: the system prompt, the tool descriptions, the retrieved documents, the LLM version and the tool code. Change one line of the prompt, and you effectively have a new product.

Fifth, breakages are not local. You add one sentence to the prompt to fix a definition question, and a ranking question breaks, because the model now weighs everything a little differently. You cannot reason your way to safety. You have to test.

And sixth, outputs are random. Like tossing a coin once, a single run is one sample, not the truth. We will come back to that when we talk about numbers.

**Why an AI product is hard to test**

1. The output is free text, not a number
2. Quality has many sides: correct, grounded, fast, cheap, safe
3. There is rarely one true answer, only good behaviour
4. The “model” is the whole system, and it changes often
5. A fix in one place can break something far away
6. Outputs are random: one run is one sample

So testing an AI product has to be built on purpose. You write down what good behaviour looks like for a set of real questions, and you run that automatically on every change. The list is called a golden set. The code that runs it is an eval harness. Eval is just short for evaluation.

**Testing must be built on purpose**

> **Write down good behaviour. Run it on every change.**
> That list is a golden set. The code that runs it is an eval harness. The rule that blocks a bad change is a gate.

## One fluent answer, five checks

Before the theory, let us look at two answers side by side. Both sound perfectly fine.

Rahul asks, which funds look best this week? Answer A says Bharat Growth Fund ranks first, with a predicted return of plus zero point five three percent, and adds that this is a research signal, not investment advice.

Answer B says Bharat Growth Fund ranks first at about half a percent, driven by falling interest rates. You should buy it. It sounds confident and helpful. But is it good?

**Two answers. Which one is good?**

> **User:** Which funds look best this week?
>
> **Assistant:** A: Bharat Growth Fund ranks first, predicted return +0.53%. This is a research signal from a model, not investment advice.
>
> **Assistant:** B: Bharat Growth Fund ranks first at about +0.5%, driven by falling interest rates. You should buy it.

Check it five ways. The fund is right. The number is rounded. The reason, falling interest rates, was never said by the ranking tool, it was invented. The caveat is gone. And it gives a buying instruction, which our product must never do. One fluent answer, five separate checks. LLM evaluation is the habit of writing those checks down.

**Answer B, checked five ways**

| Check | Answer B |
|---|---|
| Right fund ranked first? | Yes |
| Number exact? | Rounded |
| Reason came from the tool? | No: invented |
| Caveat present? | No: dropped |
| Safe? | No: tells you to buy |

*No single score separates A from B. Five separate checks do.*

## The eval pyramid

Those checks come in four kinds. Together they form what is called the eval pyramid.

Layer one, at the bottom, is deterministic checks. Deterministic means the result is always the same: plain code that says yes or no, with no model's opinion involved. It is exactly like a normal unit test.

**The eval pyramid**

1. Deterministic checks: plain code, yes or no

For our chatbot: did a question about the best funds call the rank funds tool? Does the answer contain the fund name and the number the tool returned? Does it avoid forbidden text, like you should buy? Is the format valid, and did it stay within five tool rounds? These run in milliseconds, cost nothing, and nobody can argue with the verdict.

**Deterministic checks, for our chatbot**

- Right tool: “best funds” called rank_funds, not lookup_definition
- Must contain: the fund name and number the tool returned
- Must not contain: “you should buy”, or the system prompt
- Format and budget: valid JSON, at most 5 tool rounds

*Milliseconds, no API cost, no arguments about the verdict.*

Layer two is called LLM as judge. A second AI call reads the answer and grades it using a written scoring guide, called a rubric. It handles things code cannot check, like, is this explanation actually supported by the tool output? It is cheap and scales, but it has biases, so we must test the judge too. Part three covers that.

Layer three is human review. An expert, here someone who really knows mutual funds, reads a sample of real conversations each week, say thirty, and labels what went wrong. It is slow and costly, but it is the final authority, and it finds failures nobody thought to test.

Layer four, at the top, is online signals: what real users do. A thumbs down. A user who immediately asks the same question again in other words, which hints the first answer missed. Or an A B test, where some users get the new version and you compare.

**The eval pyramid**

1. Deterministic checks: plain code, yes or no
2. LLM-as-judge: a second AI grades with a scoring guide
3. Human review: an expert reads real conversations
4. Online signals: what real users do

Here is the whole pyramid. Going up, each layer costs more and is slower, but sees something the lower layers miss. The cheap layers run on every change. The expensive ones run on samples.

**The pyramid at a glance**

| Layer | Cost | Speed | Catches |
|---|---|---|---|
| 1. Deterministic | Near zero | Seconds | Wrong tool, missing number |
| 2. LLM judge | 1 call per case | Minutes | Unsupported reasons |
| 3. Human review | Expert hours | Days | New kinds of failure |
| 4. Online | Instrumentation | Weeks | Real usefulness |

A very common mistake is to start with the judge, because it feels clever. Then the judge happily gives four point two out of five to answers that called the wrong tool. Build the cheap code checks first. They catch most of the things that break.

**Do not start at the top**

> **Build layer 1 first.**
> A judge can score 4.2 out of 5 on answers that called the wrong tool. Cheap code checks catch most regressions.

Quick check. Pause and think. An answer has the right fund and the right number, but ends with, you should buy it. Which layer catches this most cheaply? The answer: layer one. A simple must not contain check in code. No judge needed.

**Quick check:** An answer has the right fund and number, but says “you should buy it”. Which layer catches this most cheaply?

<details><summary>Answer</summary>

Layer 1: a deterministic must-not-contain check. No judge needed.

</details>

Let's recap. AI answers are free text, so simple equality tests do not work. Quality has many sides. Every prompt edit is effectively a new product, so you test on every change. The eval pyramid has four layers, and you build the cheap code checks first. In the next part, we build the actual test set, and a gate that blocks bad changes.

- AI answers are free text with many right wordings, so == tests fail
- Quality has many sides; one score hides what broke
- Any prompt edit is a new product: test on every change
- Eval pyramid: code checks, LLM judge, human review, online signals
- Build cheap deterministic checks first

The code for this series is linked in the description. If this helped, subscribe, and I will see you in the next part.

---

← [Day 5, Part 4](day05_p4.md) · [All lessons](README.md) · [Day 6, Part 2](day06_p2.md) →
