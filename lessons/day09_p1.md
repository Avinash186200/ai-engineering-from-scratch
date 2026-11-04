# Day 9, Part 1: AI System Design Interviews: The 7-Step Method

**Watch:** [youtu.be/JccSVYrQRSk](https://youtu.be/JccSVYrQRSk) · **Code:** [`day09_design/`](../day09_design/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

System design interviews for AI engineering roles feel open-ended, but they are scored on a written rubric. In this episode you learn a repeatable 7-step method that hits every part of that rubric, plus the five back-of-envelope formulas that make you sound senior.

## What you will learn

- What a system design round is, and how AI design rounds differ from classic ones
- The rubric interviewers actually score you on
- The 7-step method, with a time box for each step
- Five estimation formulas: queries per second, Little's law, token cost, storage
- The signals that move a rating from "yes" to "strong yes"

## Chapters

- [0:00](https://youtu.be/JccSVYrQRSk?t=0) Intro
- [0:21](https://youtu.be/JccSVYrQRSk?t=21) Where we are in the series
- [1:01](https://youtu.be/JccSVYrQRSk?t=61) What the design round is for
- [2:52](https://youtu.be/JccSVYrQRSk?t=172) The 7-step method
- [6:50](https://youtu.be/JccSVYrQRSk?t=410) Back-of-envelope estimates
- [8:37](https://youtu.be/JccSVYrQRSk?t=517) Signals of seniority

## Lesson notes

Slide content and the full narration, in order.

Hi, I am Avinash, and welcome to day nine of AI Engineering from Scratch. Today is about interviews. In this video, you get a simple seven step method for any AI system design question, and the arithmetic that makes your answers sound senior.

Over the last eight days, we built every part of our research assistant chatbot: the model, prompts, agents, tools, retrieval, evaluation and production. Day nine is about showing an interviewer you can put those parts together, and that people would want to work with you.

Here is the plan. This video teaches the method. The next two videos apply it to three full designs, with real numbers. The last video covers the behavioural round, where you tell stories about your own work.

**Day 9 in four videos**

- Part 1: how design rounds are scored, and the 7-step method
- Part 2: worked design: document Q&A for a large company
- Part 3: worked designs: our chatbot, and a multi-tenant platform
- Part 4: behavioural interviews with STAR

## What the design round is for

First, what is a system design interview actually testing?

You get one vague prompt, like, design a document question and answer system for our company. Your job is to turn it into an architecture: the parts, how data flows between them, how it scales, how it fails, and why you chose each piece. There is no single right answer. The interviewer is scoring how you think.

**A vague prompt, turned into an architecture**

- 35 to 60 minutes, one open prompt
- e.g. “Design a document Q&A system for our company”
- You produce: components, data flow, scale, failures, and why

*There is no single right answer. They score how you think.*

A classic design round, like a URL shortener, is about databases and caches. An AI round keeps those, but the hard part moves to the model. How does it get the right context? How does it call tools safely? How do we stop it inventing things? And what does it cost? If you spend twenty minutes on load balancers, you answered the wrong question.

**Where the hard part lives**

- **Classic design round**
  - URL shortener, news feed
  - Databases, caches, load balancers
  - Hard part: scale
- **AI design round**
  - Retrieval, tools, grounding
  - Memory, evaluation, token cost
  - Hard part: the model

*20 minutes on load balancers in an AI round = the wrong answer.*

Most companies score you on a written rubric. Problem scoping: did you ask questions before drawing? Architecture: are there clear boxes, each with one job, and no magic box labelled A I that does everything? Depth: did you go deep on the hard part, with mechanisms and numbers?

Trade-offs: for each choice, did you name the alternative and say why not? Operability: testing, monitoring, cost, security and rollback. And communication: do you check in, and adapt when the interviewer steers you? Notice what is not scored: a pretty diagram, or the number of technologies you can name.

**What interviewers actually score**

| Dimension | Strong answer |
|---|---|
| Problem scoping | Asks about users, scale, latency, data, budget first |
| Architecture | Clear boxes, one job each; no magic “AI” box |
| Depth | Goes deep on the hard part, with numbers |
| Trade-offs | Names the alternative and why not, for this context |
| Operability | Testing, monitoring, cost, security, rollback |
| Communication | Signposts, checks in, adapts when steered |

*Not scored: a pretty diagram, or how many tools you can name.*

## The 7-step method

Now the method. Use the same seven steps for every prompt. They give you structure under pressure, and they make sure you touch every line of that rubric.

Step one, clarify. The prompt is vague on purpose. Document Q and A could mean fifty files or fifty million pages. Starting without asking is the most common reason for a weak score.

**Seven steps, about 30 minutes**

1. Clarify (2 min)

Ask five things, in this order. Who are the users? What is the scale? How fast must it answer? How sensitive is the data? And is there a budget? If the interviewer says, you decide, do not stall. Say, then I will assume ten thousand employees, and correct me if that is off.

**Five questions, in this order**

> **Users · Scale · Latency · Sensitivity · Budget**
> If they say “you decide”: state an assumption out loud, write it down, move on.

Step two, requirements. Functional requirements are what the system does, like, answer questions with citations. Non functional requirements are how well: speed, accuracy, cost, security. Then two minutes of quick arithmetic, which we will see in a moment.

Step three, the high level boxes. Draw the request path left to right, and the offline jobs underneath. Then ask the interviewer: which part would you like me to go deep on? That one question hands them control, and it scores well.

**Seven steps, about 30 minutes**

1. Clarify (2 min)
2. Requirements and estimates (4 min)
3. High-level boxes (5 min)

Here are the standard boxes. A client, like a web app. An A P I layer that checks who you are. An orchestrator, the code that decides what to do next. Tools and retrieval, where facts come from. And three more: the LLM behind an adapter, so you can switch providers, a store for conversations, and logs and traces.

**Almost every LLM system looks like this**

**Client** (web, chat, Excel) → **API** (login, rate limits) → **Orchestrator** (decides next step) → **Tools + retrieval** (where facts come from)

*Plus: LLM behind an adapter · state store · logs and traces*

Step four, the deep dive. This is where your rating is decided. Breadth shows you know the words. Depth shows you have built things.

**Seven steps, about 30 minutes**

1. Clarify (2 min)
2. Requirements and estimates (4 min)
3. High-level boxes (5 min)
4. Deep dive the hard part (10 min)

In AI systems, the hard part is almost always one of these five. Retrieval, tool contracts, grounding, memory, or evaluation. Every term here was covered earlier in the series. Pick the one where the real difficulty lives, and go down to mechanisms and numbers.

**The five usual hard parts**

| Hard part | Depth sounds like |
|---|---|
| Retrieval | Chunking, hybrid search, reranking, permission filters |
| Tool contracts | Typed inputs, error rules, read-only vs write, timeouts |
| Grounding | Numbers only from tools, citations, refuse if no evidence |
| Memory | Per-conversation checkpoints, what to keep, what to forget |
| Evaluation | Golden set, a gate before release, online signals |

Step five, data and security. Cover five things quickly: who can see what, personal data, secret keys kept out of code and prompts, prompt injection, and an audit trail of who asked what.

Step six, operations. A system that cannot be tested, watched, paid for and rolled back is a demo. Mention automatic tests, an evaluation gate before any prompt change ships, tracing, cost controls, and rollback.

And step seven, trade-offs and the version one cut. Close with three sentences: the biggest trade-off you made, what ships first, and what you would add next, and what would trigger it. That shows judgement: you know what matters, and you can ship.

**Seven steps, about 30 minutes**

1. Clarify (2 min)
2. Requirements and estimates (4 min)
3. High-level boxes (5 min)
4. Deep dive the hard part (10 min)
5. Data and security (3 min)
6. Operations (3 min)
7. Trade-offs and the v1 cut (3 min)

*Leaves room for questions in a 45-minute slot.*

The repo has this as a one page template: day nine design, design template dot M D. Copy it for every practice prompt, and fill in each heading. After a few rounds, the seven steps become automatic.

**The template to practise with**

`day09_design/design_template.md`
```python
# Design: <prompt>

## 1 Clarify      users | scale | latency | sensitivity | budget
## 2 Requirements functional / non-functional
   Estimates:   queries/day, peak QPS, in flight, tokens, cost
## 3 Boxes      client, API, orchestrator, tools, LLM, state, traces
   Ask: "Where would you like me to go deep?"
## 4 Deep dive  mechanisms + numbers + failure modes
## 5 Security   permissions, PII, secrets, injection, audit
## 6 Operations CI, eval gate, tracing, cost, rollback
## 7 Trade-offs biggest trade-off | v1 | next, and when
```

## Back-of-envelope estimates

Now the arithmetic. Two minutes of numbers is where you earn the signal interviewers call, you quantify.

You need only five formulas. Queries per day. Queries per second at peak, where a peak factor of two to five is normal. Requests in flight. Cost per query from tokens. And storage. Q P S simply means queries per second.

**All the maths you need**

| Quantity | Formula |
|---|---|
| Queries per day | users × fraction active × questions each |
| Peak QPS | per day ÷ busy seconds × peak factor (2 to 5) |
| In flight | arrival rate × seconds per request |
| Cost per query | in tokens × in price + out tokens × out price |
| Storage | items × size each (vector: dims × 4 bytes) |

The one with a name is Little's law. Think of an I R C T C ticket counter. If two people arrive every minute, and each takes five minutes, about ten people are being served at any moment. For a server: one point six requests a second, eight seconds each, means about thirteen in flight.

**How many requests are in flight?**

> **In flight = arrival rate × time each takes**
> Like an IRCTC queue: 2 people arrive per minute, each takes 5 minutes → about 10 at the counters.

Watch it work. Ten thousand employees, thirty percent active, five questions each, is fifteen thousand a day. Over an eight hour day, that is about half a query per second. Times three for the peak, about one point six. Thirteen in flight. A few small servers handle that easily, so load is not the problem.

**10,000 employees asking questions**

| Step | Arithmetic |
|---|---|
| Per day | 10,000 × 30% × 5 = 15,000 questions |
| Average QPS | 15,000 ÷ 28,800 s (8 hours) = 0.52 |
| Peak QPS | 0.52 × 3 ≈ 1.6 |
| In flight | 1.6 × 8 s ≈ 13 |

*13 in flight: a few servers. The real limit is the LLM provider.*

And that is the real point. Every estimate must end in a decision. At two queries a second, you do not need a queue. At ninety calls a second, you do. Say it out loud: that number tells me the constraint is cost, not compute.

**Let the numbers drive decisions**

> **“That number tells me the constraint is cost, not compute.”**
> Every estimate should end in a decision: a queue or not, a cache or not, one database or many.

## Signals of seniority

Finally, what moves a rating from yes, to strong yes?

Five signals. You quantify. You design for failure: what happens when the model provider is down, or retrieval finds nothing? You cut scope, with a small first version. You bring real lessons from things you built. And you are honest about uncertainty. I would want to measure that first, is a senior answer.

**What senior answers sound like**

- You quantify, and the numbers drive choices
- You design for failure: provider down, no results, tool timeout
- You cut scope: a v1 that ships in weeks, then what next
- You bring real lessons from systems you have built
- You say “I would want to measure that before choosing”

Quick check. Pause and answer: the interviewer says, design a chatbot over our documents. What do you do in the first two minutes? The answer: you clarify. Users, scale, latency, sensitivity, budget. State your assumptions out loud. No boxes yet.

**Quick check:** An interviewer says “Design a chatbot over our documents.” What do you do in the first two minutes?

<details><summary>Answer</summary>

Clarify: ask about users, scale, latency, data sensitivity and budget, and state assumptions out loud. No boxes yet.

</details>

Let's recap. In an AI design round, the hard part is the model. You are scored on scoping, architecture, depth, trade-offs, operability and communication. The seven steps cover all of them. Five formulas give you the numbers, and every number should end in a decision. Next video, we use all of this on a full design: document question and answer for ten thousand employees.

- AI design rounds: the hard part is the model, not load balancers
- Scored on scoping, architecture, depth, trade-offs, operability, communication
- 7 steps: clarify, requirements, boxes, deep dive, security, ops, v1 cut
- Five formulas; Little's law for requests in flight
- Every estimate must end in a design decision

The template is in the repo, linked in the description. If this helped, subscribe, and I will see you in the next video.

---

← [Day 8, Part 4](day08_p4.md) · [All lessons](README.md) · [Day 9, Part 2](day09_p2.md) →
