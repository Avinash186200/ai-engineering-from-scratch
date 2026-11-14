# Interview Special: 10 AI Agent Interview Questions

Video (8.8 min, no intro): [AI Agent Interview Questions (2026): Memory, Caching, Routing + 7 More, With Answers](https://youtu.be/_rVcMiSIjro)

Questions about AI agents in production, the kind asked after the basics. Each has a model answer you can say in
under a minute. Try each one out loud before you read the answer. The basics (LLMs, hallucination, JSON output,
prompt injection, tool calling) are in [Day 10, Part 1](https://youtu.be/Y6tVgVUjuUA) and [`day10_mock/`](../day10_mock/).

Every answer has the same shape: a one-line concept, the general approach in 3 to 5 points, an example from
something you built, and one honest limit. Then stop talking.

## 1. Tell me about the AI system you built. You have 30 seconds.

[Watch at 0:16](https://youtu.be/_rVcMiSIjro?t=16)

**Four layers, then stop**

Use four layers. One, who uses it: for example a chat app and an Excel add-in. Two, the app: an agent service that saves conversation state in a database. Three, what it can do: tools for numbers, and retrieval over documents. Four, where it runs: containers in the cloud, with CI and monitoring. Then stop, and say: happy to go deeper on any layer. Thirty seconds, and the interviewer chooses where to dig.

> Then: “Happy to go deeper on any layer.”

## 2. Would you build this with one agent or several agents?

[Watch at 1:01](https://youtu.be/_rVcMiSIjro?t=61)

**Start with one. Split when the jobs differ.**

Start with one agent. Every handoff between agents adds tokens, delay, and another place to fail. I split only when the jobs really differ: different tools, different permissions, or work that can run in parallel. Then the usual shape is a supervisor that hands tasks to specialists. And the evals decide, not the hype: I split when one agent measurably fails.

> Let the evals decide: split when one agent measurably fails.

## 3. How would you design memory for an agent, at the user level and the organisation level? How do you forget?

[Watch at 1:37](https://youtu.be/_rVcMiSIjro?t=97)

**The model forgets. The app remembers.**

The model remembers nothing between calls, so memory is something the app builds. Short term is the current thread: save it after every step, and when it gets long, keep the recent turns and summarise the rest. Long term is across threads: preferences, past work, standing rules, stored as small notes with embeddings. User and organisation memory live in separate namespaces, and a user's memory never flows into the shared space by itself.

> User memory never flows into the org space by itself.

**Using memory, and forgetting it**

For each question, pull only the top few memories, scored by relevance, recency and importance, inside a token budget. To forget: expiry dates for short lived items, overwrite when a fact changes, decay for things never used, and users can delete their own. One limit to say out loud: memory goes stale, so it never overrides fresh data. Numbers always come from today's tools.

> Limit: memory can go stale. It never overrides fresh data.

## 4. Users ask the same or similar questions again and again. How do you cut LLM cost and keep context?

[Watch at 2:59](https://youtu.be/_rVcMiSIjro?t=179)

**Layer it**

I layer it. An answer cache, exact or semantic, so a repeated question skips the model call. Key it by the user's permissions and the data date, so yesterday's answer never comes back today. Then provider prompt caching: keep the system prompt and tool definitions fixed at the front, and they cost a fraction on repeat calls. Keep context small: recent turns plus a summary. And measure the hit rate. One rule: use a strict threshold, and never cache match a question that needs a number.

> Never cache-match a question whose answer is a number.

## 5. How do you route a request to a different LLM based on how hard it is?

[Watch at 3:52](https://youtu.be/_rVcMiSIjro?t=232)

**Four ways to decide, one safety net**

There are four ways to decide. Simple rules on intent. A small classifier trained on labelled questions. A cascade, where the cheap model answers first, a check validates it, and it escalates to the strong model if the check fails. Or a small model acting as the router. I start with rules, then add a cascade once I know where the rules fail. Measure accuracy and cost per route on an eval set. And the safety net matters more than the router: when unsure, or when the answer is a number, go to the strong model.

> The fallback matters more than the router.

## 6. How do you stop your AI from hallucinating?

[Watch at 4:42](https://youtu.be/_rVcMiSIjro?t=282)

**You can't remove it. Make it rare and detectable.**

You can't eliminate it, so you make it rare and detectable. First, ground it: every number comes from a tool, and every explanation from retrieved documents, with citations. If nothing relevant comes back, it says I don't know. Second, check every answer in code: each number must appear in the tool output, and each citation must match a retrieved chunk. Third, measure: a fixed set of real questions before every release, and a judge on a sample in production. And temperature zero does not fix hallucination. Grounding does.

> Temperature zero does not fix it. Grounding does.

## 7. What is context engineering, and how is it different from prompt engineering?

[Watch at 5:32](https://youtu.be/_rVcMiSIjro?t=332)

**Deciding what goes into the window, every call**

Prompt engineering is how you word the instruction. Context engineering is deciding what goes into the window on every call: which documents, which tools, which memories, how much history. I give each section a token budget, put the stable parts first so they cache, and the user's question last. And fewer, better chunks beat more chunks, because models miss facts buried in a long prompt. More context is not better context.

> More context is not better context.

## 8. How do you evaluate an AI agent?

[Watch at 6:13](https://youtu.be/_rVcMiSIjro?t=373)

**Grade the answer and the path**

Grade the answer and the path. The answer: correct, grounded, cited. The path: did it pick the right tool, with the right arguments, in a sensible number of steps, at a sensible cost. I run a golden set built from real questions on every change, and use an LLM judge with a written rubric for the open ended parts. But I check the judge against human grades on a sample, because judges favour long answers and their own style.

> An agent that is right by luck still fails the test.

## 9. Your model needs to know new company facts. Fine-tune it, or use RAG?

[Watch at 6:52](https://youtu.be/_rVcMiSIjro?t=412)

**Facts go in retrieval. Behaviour can go in weights.**

For facts, RAG. Facts change, and in retrieval they stay current and citable: update the index tonight and the answer changes tomorrow. Fine tuning bakes facts into weights, where you can't cite them and they go stale. I'd fine tune for a narrow, high volume task, or a format that prompting can't hold. The order is: prompting first, then RAG, then fine tuning.

> Try prompting first, then RAG, then fine-tuning for narrow tasks.

## 10. What guardrails do you put around an LLM in production?

[Watch at 7:31](https://youtu.be/_rVcMiSIjro?t=451)

**Checks on both sides, in code**

Checks on both sides. Before the model: catch injection attempts, mark retrieved text as data, strip personal data, and refuse questions you don't support. After the model: validate the format with a schema, check every number against the tool result, and block unsafe content. Give tools the least privilege they need. And put these checks in code, not just in the prompt. A prompt is a request. Code is a rule.

> A prompt is a request. Code is a rule.

## The 30-second versions (Shorts)

One a day at 7 PM IST, all in the [Interview Prep playlist](https://www.youtube.com/playlist?list=PLO8FrBIinbsY).

| Short | Link |
|---|---|
| Prompt caching | https://youtube.com/shorts/fgpbxVw1LB4 |
| The semantic cache trap | https://youtube.com/shorts/YwLXOvNy0xM |
| Why AI hallucinates | https://youtube.com/shorts/ASWoEX3jK_M |
| Agent memory | https://youtube.com/shorts/lI7nt5ILwsQ |
| Model routing | https://youtube.com/shorts/CjWx2l4-_yk |
| Context engineering | https://youtube.com/shorts/EkB-EEKp2FQ |
| Fine-tuning won't teach new facts | https://youtube.com/shorts/E45MTqJQGzI |
| 5 layers against hallucination | https://youtube.com/shorts/DH-0dhrJcic |
| One agent or many? | https://youtube.com/shorts/EBvuwzYUe7I |
| Explain any AI system in 4 layers | https://youtube.com/shorts/Vze1io6lIoI |
| How to test an AI agent | https://youtube.com/shorts/bMUNMEsr7eU |
| LLM-as-a-judge | https://youtube.com/shorts/R2UH-hjVsOA |
| Do you still need RAG? | https://youtube.com/shorts/mRD3ykW6h9A |
| MCP vs function calling | https://youtube.com/shorts/9tUeSW4vZpU |
| Guardrails on both sides | https://youtube.com/shorts/9DHz8qi8nSU |
| "Any questions for us?" | https://youtube.com/shorts/qNHYf_1V-Ko |
