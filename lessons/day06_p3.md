# Day 6, Part 3: Measuring LLM Quality: Hallucination Rate, LLM-as-Judge, Kappa

**Watch:** [youtu.be/6GZ9wKMMkZw](https://youtu.be/6GZ9wKMMkZw) · **Code:** [`day06_evals/`](../day06_evals/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

How do you put real numbers on the quality of an AI agent? In this episode we measure our research assistant chatbot properly: tools, cost, hallucination, and judges you can trust.

## What you will learn

- The metrics that matter for an agent: tool choice, arguments, latency, cost per completed task
- Why p95 latency tells you more than the average
- How to measure hallucination rate by checking claims one by one
- LLM-as-judge: rubrics, known biases, and calibration with Cohen's kappa
- Why 10 out of 10 does not mean 100% quality: confidence intervals and flaky tests

## Chapters

- [0:00](https://youtu.be/6GZ9wKMMkZw?t=0) Intro
- [0:27](https://youtu.be/6GZ9wKMMkZw?t=27) Agent metrics
- [1:36](https://youtu.be/6GZ9wKMMkZw?t=96) Latency and cost
- [3:24](https://youtu.be/6GZ9wKMMkZw?t=204) Measuring hallucination rate
- [5:08](https://youtu.be/6GZ9wKMMkZw?t=308) LLM as judge
- [6:40](https://youtu.be/6GZ9wKMMkZw?t=400) Calibrating the judge
- [7:38](https://youtu.be/6GZ9wKMMkZw?t=458) Confidence intervals and flaky tests

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In part two we built a golden set and a gate that blocks bad changes. Now we put real numbers on quality: what to measure for an agent, how to measure hallucination, and how far to trust an AI judge.

There is a little arithmetic in this one, but every number is worked through slowly, with examples.

## What to measure for an agent

Remember, an agent is an AI that decides which tools to call, in a loop, until it can answer. So its quality is more than the final text.

First, tool selection. Out of all the cases, how often did the agent call the tool a correct answer needs? Our harness already measures this.

Second, argument correctness. Rank funds as of the eighteenth of June, top five. If the agent calls the right tool but forgets the date, it uses today's date, and gives a plausible, wrong answer. Only an argument check catches that.

Then groundedness: is every claim backed by what the tool returned? Steps per task, because rising steps mean the agent is confused or looping. Error handling: when a tool fails, does it say so instead of guessing? And safety, which must always be one hundred percent.

**Metrics for an agent**

| Metric | The question it answers |
|---|---|
| Tool selection | Did it call the right tool? |
| Argument correctness | Were the tool's inputs right: date, top_n? |
| Groundedness | Is every claim backed by tool output? |
| Steps per task | How many rounds? Rising = confused |
| Error handling | When a tool fails, does it say so? |
| Safety | Injection resisted? No leaks? Must be 100% |

Now speed. Take ten response times. The mean is three point four six seconds, but that describes nobody: it is dragged up by one slow request of nine point eight seconds. The median, also called p fifty, is two point seven five. And p ninety five, the time that ninety five percent of requests beat, is about seven point three seconds.

**Ten response times, in seconds**

- Request 1: 1.8s
- Request 5: 2.6s
- Request 9: 4.2s
- Request 10: 9.8s

*Mean 3.46s describes nobody. Median (p50) 2.75s. p95 about 7.3s.*

A percentile is the value below which a given share of requests falls. p ninety five is what the slowest one in twenty users feels, and users remember slow answers. In an agent, the slow tail usually means an extra tool round. You need hundreds of requests for this number to be stable, not ten.

**Watch p95, not the average**

> **p95 = what the slowest one in twenty users feels.**
> In agents the slow tail usually means an extra tool round. Open that trace to see why.

Now money. Model B is sixty percent cheaper per call. But it needs more calls per task, and gets only seventy tasks right instead of ninety. Divide total spend by correct tasks. Model A costs two rupees thirteen paise per completed task. Model B costs two rupees twenty nine. The cheaper model is more expensive per useful answer.

**Cost per completed task, 100 tasks each**

|  | Model A | Model B |
|---|---|---|
| Price per call | ₹1.60 | ₹0.64 (60% cheaper) |
| Calls per task | 1.2 | 2.5 |
| Total spend | ₹192 | ₹160 |
| Tasks done correctly | 90 | 70 |
| Cost per completed task | ₹2.13 | ₹2.29 |

So the number to track is cost per completed task: total spend, divided by tasks actually finished correctly. The invoice shows cost per request. The business cares about cost per useful answer. And thirty analysts out of a hundred with no useful answer is a cost too.

**Cost per completed task**

> **Total spend ÷ tasks finished correctly**
> Cost per request is what the invoice shows. Cost per completed task is what the business pays.

## Measuring hallucination

Next, the question everyone asks: does it hallucinate? As asked, that is not measurable. Here is how to turn it into a number.

Remember, a hallucination is a fluent statement that is false, or not backed by any source. Step one, split the answer into single facts, called claims. Step two, gather the evidence the system actually had: tool results and retrieved documents. Step three, label each claim. Step four, divide the bad claims by all claims.

**Four steps to a hallucination rate**

1. Split the answer into single, checkable claims
2. Collect the evidence the system actually saw
3. Label each claim: supported, unsupported, contradicted
4. Rate = (unsupported + contradicted) ÷ all claims

Here is an answer about our fund ranking. Five claims are supported by the tool output. But driven by falling interest rates: the tool never said anything about reasons. Unsupported. And proven live edge: the tool's caveat says the opposite. Contradicted. Two out of seven, so twenty eight point six percent. Notice, every number was correct. The risk had moved into the explanation.

**One answer, seven claims**

| Claim in the answer | Label |
|---|---|
| Bharat Growth Fund ranks first | Supported |
| Predicted return +0.53% | Supported |
| Ranked out of 120 funds | Supported |
| Model used: the gradient-boosted ranker | Supported |
| As of 19 June 2025 | Supported |
| Driven mainly by falling interest rates | Unsupported |
| The model has a proven live edge | Contradicted |

*2 bad claims ÷ 7 = 28.6%. All five numeric claims were right.*

A common mistake is to check claims against what is true in the world. Maybe interest rates really did fall. It is still a hallucination for this system, because nothing the system saw said so. In a financial product, unsupported is the failure. Numbers can be checked by code: every figure in the answer must appear in the tool output.

**True in the world is not enough**

> **Unsupported is the failure, not only false.**
> Check claims against the evidence the system had, not against general knowledge.

## LLM-as-judge, done properly

To label claims like driven by falling interest rates at scale, you need a judge. Let us build one properly.

A rubric is the judge's marking scheme. Three rules. Score one thing at a time, here faithfulness only, not tone. Anchor every score with a concrete description: four equals good is useless. And ask the judge to list the unsupported claims first, then give the score. That makes it more consistent, and gives you something to debug.

**Faithfulness, scored 1 to 5**

| Score | Meaning |
|---|---|
| 5 | Every claim supported; numbers exact; caveat present |
| 4 | All supported; one harmless rounding |
| 3 | Facts right, but one invented reason or missing caveat |
| 2 | A wrong number or rank, or the caveat contradicted |
| 1 | Ignores the tool, or obeys an injected instruction |

There are two ways to judge. Pointwise scores one answer on its own, which is easy to track over time. Pairwise shows the judge two answers, say from the old and new prompt, and asks which is better. Like a cricket selector, it is easier to say who is better than to give an exact score.

**Pointwise vs pairwise**

- **Pointwise**
  - Score one answer: faithfulness = 4
  - Easy to track and threshold
  - Use for gates and dashboards
- **Pairwise**
  - Show two answers: which is better?
  - Relative is easier than absolute
  - Use when choosing a new prompt

Judges have known biases. They favour whichever answer is shown first, so run both orders. They like long answers, so say length is not merit. They prefer text from their own model family, so use a different family as judge. They vary between runs. And if judge and writer share a misconception, the judge will not catch it.

**Biases, and what to do about them**

| Bias | Fix |
|---|---|
| Position: favours first answer | Run both orders; win only if both agree |
| Verbosity: favours long answers | Rubric says length is not merit |
| Self-preference: likes its own family | Judge with a different model family |
| Inconsistency between runs | Low randomness; reason before score |
| Shared blind spots | Code checks on numbers; human review |

A judge is a measuring instrument, so check it against a human first. Here an analyst and the judge both grade twenty answers. They agree on sixteen, eighty percent. That sounds good. But when most answers pass, two raters who just say pass to everything also agree a lot, purely by chance.

**Judge vs analyst, 20 answers**

|  | Analyst: pass | Analyst: fail |
|---|---|---|
| Judge: pass | 12 | 3 |
| Judge: fail | 1 | 4 |

*They agree on 16 of 20 = 80%. Sounds good. Is it?*

Cohen's kappa corrects for that. The judge says pass seventy five percent of the time, the analyst sixty five. So chance alone gives zero point five seven five agreement. Kappa is how far above chance we are: zero point five three, only moderate. Worse, the judge passed three of the seven bad answers. Tighten the rubric and measure again before it gates anything.

**Working out kappa**

1. Observed agreement: 16 ÷ 20 = 0.80
2. Chance agreement: 0.75×0.65 + 0.25×0.35 = 0.575
3. Kappa = (0.80 − 0.575) ÷ (1 − 0.575) = 0.53
4. 0.53 = moderate. Above 0.6 is substantial

*Worse: the judge passed 3 of the 7 bad answers.*

## How much to trust a score

Last chapter. How much should you trust a pass rate at all?

A pass rate from a small set is an estimate, like guessing a batter's average from a few innings. The Wilson interval gives the likely range. Ten out of ten could mean a true pass rate as low as seventy two percent. Four times more cases roughly halves the width. Quoting the range, not just the score, is a mark of seniority.

**Pass rate and its 95% range (Wilson)**

| Result | Pass rate | True rate is likely between |
|---|---|---|
| 10 / 10 | 100% | 72% and 100% |
| 46 / 50 | 92% | 81% and 97% |
| 184 / 200 | 92% | 87% and 95% |

*Ten perfect cases are consistent with a true pass rate near 72%.*

When comparing an old and new prompt, forty two against forty five out of fifty proves little on its own. Compare case by case, and investigate anything that flipped from pass to fail. And since outputs are random, run each case several times. A case passing three out of five is flaky. It means the prompt is unclear for that question. Fix the cause.

**Comparing versions, and flaky cases**

- Old prompt 42/50, new 45/50: the ranges overlap heavily
- Compare case by case: which flipped pass to fail?
- Run each case 3 to 5 times with a real model
- 5/5 is stable; 3/5 is flaky: fix the cause, do not retry

Quick check. A judge agrees with your analyst eighty percent of the time. Can it gate releases? Pause. The answer: not yet. Compute kappa, here only zero point five three, and check how many bad answers it catches, here four of seven. Improve it first.

**Quick check:** A judge agrees with your analyst on 80% of answers. Can it gate releases?

<details><summary>Answer</summary>

Not yet. Compute kappa (here 0.53, moderate) and check how many bad answers it catches (4 of 7).

</details>

Let's recap. For agents, measure tool choice, arguments, steps, error handling and safety. Watch p ninety five latency and cost per completed task. Hallucination rate is bad claims divided by all claims, checked against the evidence. Judges need a clear rubric and calibration with kappa. And always report a range. In the final part, we watch the live system: traces, monitoring and guardrails.

- Agents: measure tool choice, arguments, steps, errors, safety
- Watch p95 latency and cost per completed task
- Hallucination rate = bad claims ÷ all claims, against evidence
- Judges need one-dimension rubrics and kappa calibration
- Report pass rates with a range; rerun to find flaky cases

The code for this series is linked in the description. If this helped, subscribe, and I will see you in the next part.

---

← [Day 6, Part 2](day06_p2.md) · [All lessons](README.md) · [Day 6, Part 4](day06_p4.md) →
