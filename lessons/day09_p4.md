# Day 9, Part 4: Behavioural Interviews with STAR: Answers That Score

**Watch:** [youtu.be/v6alpjpjH54](https://youtu.be/v6alpjpjH54) · **Code:** [`day09_design/`](../day09_design/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Behavioural interviews ("tell me about a time when...") are scored against a list of competencies. In this episode you learn the STAR structure, how to build a small story bank that covers most questions, and short scripts for the questions that trip people up.

## What you will learn

- What behavioural interviewers score, and the three things they listen for
- STAR: Situation, Task, Action, Result, with a worked two-minute story
- Weak versus strong results, and the "we" versus "I" honesty rule
- A five-story bank, and how to tell a mistake or a disagreement story
- Scripts for "tell me about yourself", "I don't know", your first 90 days, and questions to ask

## Chapters

- [0:00](https://youtu.be/v6alpjpjH54?t=0) Intro
- [0:17](https://youtu.be/v6alpjpjH54?t=17) What the interviewer is scoring
- [1:15](https://youtu.be/v6alpjpjH54?t=75) The STAR structure
- [3:58](https://youtu.be/v6alpjpjH54?t=238) Your story bank
- [6:00](https://youtu.be/v6alpjpjH54?t=360) Scripts for tricky moments

## Lesson notes

Slide content and the full narration, in order.

Welcome back. Last time we designed a chatbot with tools and a multi tenant agent platform. That was the design round. Now the other round that decides offers: the behavioural interview.

## What the interviewer is scoring

First, what is actually being scored?

A behavioural question asks about something you actually did, like, tell me about a time when. The idea is that past behaviour predicts future behaviour. The interviewer writes notes against a list: ownership, judgement, dealing with ambiguity, conflict, leadership, communication and integrity. For senior roles, also how big the thing was, and how you changed what others did.

**“Tell me about a time when…”**

- Idea: past behaviour predicts future behaviour
- Scored on: ownership, judgement, ambiguity, conflict
- …and leadership, communication, integrity
- Senior roles: extra weight on scope and influence

In every answer, they listen for three things. What you personally did, not the team. Why you chose it, which shows judgement. And what happened, a concrete result. Rambling, saying we with no I, and ending with, and it went well, all score low.

**Three things they listen for**

> **What YOU did · WHY you chose it · WHAT happened**
> Low scores: rambling, “we” with no “I”, and endings like “and it went well”.

## The STAR structure

The fix is a four part structure called STAR.

S is the situation: one sentence of context, just enough. T is the task: one sentence on what you owned. Most people spend half their answer here. Do not.

A is the action, the bulk: four or five sentences on your decisions and why. R is the result: a concrete outcome, and the lesson you carried forward. Two minutes is the ceiling, about two hundred fifty words. Stop at the result, and let them ask follow ups. A story that ends early invites good questions.

**Four parts, about two minutes**

| Part | Length | Content |
|---|---|---|
| Situation | 1 sentence | Who, what, why it mattered |
| Task | 1 sentence | What you owned |
| Action | 4–5 sentences | Your decisions and trade-offs; say “I” |
| Result | 2 sentences | A concrete outcome, plus the lesson |

*Two minutes is the ceiling: about 250 spoken words.*

Here is a worked example, a made up story about an engineer called Priya, so you can hear the shape. Situation: her team produced a weekly fund report that forty analysts relied on.

Task: she owned a change to how dates were stored in the source table.

Action. Her change passed its own tests, but another report read the old date format, and showed blanks for a day. She did three things, in order. First, rolled back, to restore service before doing anything clever. Then traced the real cause, instead of patching the symptom. Then fixed both the data and the schema, and told the team plainly what happened.

Result: service restored the same day, and a standing rule: before changing a table, check every program that reads it. The lesson: a change can pass its own checks and still break someone else's assumptions.

**“Tell me about a mistake you made”**

1. S: Priya's team shipped a weekly fund report used by 40 analysts in Gurugram
2. T: She owned a change to how dates were stored in the source table
3. A: Change passed its tests, but a downstream report read the old format
4. A: She rolled back first, then traced the real cause, then fixed data and schema
5. R: Restored the same day; new rule: check every reader before changing a table

Compare the endings. Weak: we fixed it, and the team was happy. Strong: we rolled back the same day, fixed the data and schema, and I added a rule that we have followed since. The strong version has an outcome, a mechanism, and a lesson that changed behaviour.

**Weak versus strong**

- **Weak**
  - “We fixed it and the team was happy.”
  - No mechanism
  - No lesson
- **Strong**
  - “Rolled back the same day, fixed data and schema”
  - “Added a rule: check every reader first”
  - “We have followed it since”

One common mistake: saying I for everything, including team work. Use we built for team work, I built only for what you did yourself, and I led for what you owned. Interviewers probe details, and inflated ownership falls apart at the second question.

**The honesty rule for “I” and “we”**

> **“We built” for team work · “I built” for what you did · “I led” for what you owned**
> Interviewers probe details. Inflated ownership collapses at the second question.

## Your story bank

You do not need fifty stories. You need about five, each able to answer many questions.

Build five. A system you built end to end. A time you told an uncomfortable truth, like saying a model's results were weaker than people hoped. A mistake. A disagreement. And growing a team, or helping someone else grow. Between them, they cover most questions you will be asked.

**One story, many questions**

| Story | Use it for |
|---|---|
| A system you built end to end | Biggest achievement, technical leadership |
| Telling an uncomfortable truth | Integrity, pushing back on pressure |
| A mistake or incident | Failure, ownership, learning |
| A disagreement | Conflict, receiving feedback |
| Building or growing a team | Leadership, hiring, mentoring |

Two tips for the tricky ones. For a mistake, say how big it was before they ask, for example, this was the test system, not production. Being precise about scope is part of a good answer. For a disagreement, the strongest stories are often ones where you were wrong: you understood why the rule existed, tested the claim, and adopted the fix quickly.

**Mistakes and disagreements**

- Mistake: state the blast radius first: “this was test, not production”
- Accuracy about scope is itself part of a good answer
- Disagreement: understand the rule, test the claim, reply with evidence
- Being wrong and adopting the fix quickly builds trust

Tell me about yourself is usually the first question, and it sets the frame. Start in the present: your role and its scale. Then one signature system. One sentence on how you got here. The thread that connects it all. And what you want next. Never start fifteen years ago and walk forward; they stop listening.

**Two minutes, in this order**

1. Present: your role and its scale
2. One signature system you built
3. How you got here, in one sentence
4. The thread through your career
5. What you want next, and why this role

*Never start in 2010 and walk forward year by year.*

What is your weakness? A good answer has four properties. It is real: fake weaknesses like, I work too hard, are discounted immediately. It is relevant to the role, like a gap in a newer part of the stack. You are already fixing it, with a concrete step, such as a structured course or a project. And that fix itself shows a strength: you assess yourself honestly.

**Real, relevant, already being fixed**

- Real: not “I work too hard”; interviewers discount that instantly
- Relevant to the role, e.g. a skill gap in a newer area
- Already being fixed, with a concrete step you are taking
- The fix shows a strength: you measure yourself honestly

## Scripts for tricky moments

Finally, short scripts for the moments that trip people up.

You will be asked about a tool you have never used. Never bluff, because the second question exposes it, and then everything else you said is doubted. Use four parts. I have not used it directly. The problem it solves is this. I would evaluate it like this. And the closest thing I have done is that.

**Never bluff. Use four parts.**

> **“I haven't used that directly. The problem it solves is X. I'd evaluate it by Y. The closest I've done is Z.”**
> A bluff is exposed by the second question, and then everything you said is doubted.

For example: have you used a reranker in production? Not in production. It improves rough vector relevance by reading the question and passage together, on the top fifty only. I would measure precision on a golden set, with and without it, plus the delay it adds. The closest I have done is comparing keyword, vector and hybrid search on labelled questions.

**“Have you used a reranker in production?”**

> **User:** Have you used a reranker in production?
>
> **Assistant:** Not in production. It fixes rough vector relevance by reading question and passage together, on the top 50 only. I'd measure precision at top 8 on a golden set, with and without it, plus added latency. Closest: I compared keyword, vector and hybrid search on a labelled set.

For leadership questions, use a pattern: a principle, a concrete practice, an example. How do you hire? Give a realistic problem with a hidden trap, like a dataset that leaks the future. Standards? Put them in the process, like required tests, not in your head. Mentoring? Pair on real work. And saying no? Always with an alternative: not like that, but here is how we get there by Thursday.

**Principle, practice, example**

- Hiring: a realistic problem with a hidden trap; do they find it?
- Standards: put them in the process, not in your head
- Mentoring: pair on real work; ask what would make this wrong
- Saying no: always with an alternative and a date

If asked about your first ninety days: learn for thirty, measure for thirty, deliver for thirty. Close with one line: I would rather earn the right to change things by measuring first.

**Learn, measure, deliver**

| Days | Focus |
|---|---|
| 1–30 | Learn: users, system, incident history; ship one small fix |
| 31–60 | Measure: the evaluation set and key metrics; find the biggest gap |
| 61–90 | Deliver: one real improvement, proven by the evaluation |

*“I'd rather earn the right to change things by measuring first.”*

And at the end, you get to ask. Pick two or three questions. Technical ones for engineers: what does your evaluation set look like? What was your last LLM incident, and what changed? Success questions for managers: what would make someone clearly successful at six months?

**Questions that impress**

- What does your evaluation set look like, and how does a change reach production?
- What is the biggest open problem in the system I'd work on?
- What was the last LLM incident, and what changed afterwards?
- What would make someone clearly successful here at six months?

Quick check. Pause and answer: your story ends with, and it went really well. What is missing? The answer: a concrete result and a lesson. Add a real outcome, like a number or a decision, how it was achieved, and what you now do differently.

**Quick check:** Your story ends: “…and it went really well.” What is missing, and how do you fix it?

<details><summary>Answer</summary>

A concrete result and a lesson. Add an outcome (a number, a shipped system, a decision), the mechanism, and what you now do differently.

</details>

Let's recap. Interviewers score what you did, why, and what happened. STAR keeps every story under two minutes. Five stories cover most questions, told honestly. Never bluff. And rehearse each story out loud with a timer. Tomorrow, day ten, we put it all together in full mock interviews, including coding rounds.

- They score: what you did, why, and what happened
- STAR: 1 sentence, 1 sentence, 4–5 sentences, 2 sentences
- Five stories cover most questions; say “we” and “I” honestly
- Never bluff: say it, explain it, how to evaluate, closest thing
- Rehearse each story aloud, under two minutes

The design template and practice prompts are in the repo, linked in the description. Subscribe, and I will see you on day ten.

---

← [Day 9, Part 3](day09_p3.md) · [All lessons](README.md) · [Day 10, Part 1](day10_p1.md) →
