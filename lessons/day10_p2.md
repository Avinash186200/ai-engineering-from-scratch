# Day 10, Part 2: AI System Design Mock Interview: Company Document Q&A (RAG)

**Watch:** [youtu.be/Jc6eLHTTZ9M](https://youtu.be/Jc6eLHTTZ9M) · **Code:** [`day10_mock/`](../day10_mock/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

A full system design mock interview, minute by minute: design a question-answering assistant over a company's internal documents for 10,000 employees.

## What you will learn

- How to spend 35 minutes: the 7-step method with a minute budget
- Clarifying questions and stating assumptions out loud
- The deep dive: chunking, hybrid search, reranking, grounded answers with citations
- Permissions, prompt injection, cost and the golden set as a deploy gate
- The ten probes interviewers ask, with model answers

## Chapters

- [0:00](https://youtu.be/Jc6eLHTTZ9M?t=0) Intro
- [0:56](https://youtu.be/Jc6eLHTTZ9M?t=56) The 35-minute run sheet
- [1:38](https://youtu.be/Jc6eLHTTZ9M?t=98) Clarify and requirements
- [2:49](https://youtu.be/Jc6eLHTTZ9M?t=169) Boxes and the deep dive
- [2:57](https://youtu.be/Jc6eLHTTZ9M?t=177) High-level boxes
- [3:28](https://youtu.be/Jc6eLHTTZ9M?t=208) Deep dive: retrieval
- [4:30](https://youtu.be/Jc6eLHTTZ9M?t=270) Security, operations and the v1 cut
- [5:44](https://youtu.be/Jc6eLHTTZ9M?t=344) Operations and cost
- [6:35](https://youtu.be/Jc6eLHTTZ9M?t=395) The probes

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In the last part we ran the technical screen, with short two minute answers. Now the big one: the system design round, where you get one open problem and thirty five minutes.

Here is the prompt. Design an assistant that lets ten thousand employees of a company ask questions over its internal documents, things like policies, wikis and contracts, and get accurate answers with sources. Pause here and try the first five minutes yourself.

**Your design question**

> **Design an assistant that lets 10,000 employees ask questions over the company's internal documents, with accurate, cited answers.**
> Policies, engineering wikis, contracts, research notes. You have 35 minutes.

One thing to understand before you start. The interviewer is scoring your reasoning, not the picture. Every box you draw needs a one sentence reason, and wherever there was a choice, you say the trade off out loud.

**They score your reasoning, not the diagram**

> **Every box needs a one-sentence reason.**
> And wherever there was a choice, say the trade-off out loud.

## The 35-minute run sheet

On Day nine we learned a seven step design method. Here it is again, with a minute budget for each step.

Clarify for two minutes. Requirements for two. High level boxes for five. Then ten minutes on the deep dive, the hardest part. Three on data and security, three on operations, and three on trade offs and the first version. That is about twenty eight minutes, which leaves a buffer. If you are still drawing boxes at minute fifteen, you will not get to the deep dive.

**Seven steps, with a clock**

| Minutes | Step | Output |
|---|---|---|
| 0 – 2 | 1. Clarify | Assumptions written at the top |
| 2 – 4 | 2. Requirements | Functional + non-functional list |
| 4 – 9 | 3. High-level boxes | Two paths, each box has a reason |
| 9 – 19 | 4. Deep dive | The hard part, in detail |
| 19 – 22 | 5. Data and security | Permissions, injection, audit |
| 22 – 25 | 6. Operations | Evals, tracing, cost, rollback |
| 25 – 28 | 7. Trade-offs, v1 cut | What ships first, and why |

*About 28 minutes, leaving a buffer to 35.*

## Clarify and requirements

Let's walk through it. Step one: clarify. Ask questions, and then state your assumptions so the interviewer can correct them.

For example: I will assume twenty percent of employees use it each day, with five questions each, so about ten thousand questions a day. Hundreds of thousands of documents, changing daily. A few seconds is fine for a first answer. HR and legal documents have access controls. And, is there a budget? Saying the assumption earns the credit; the exact number matters less.

**Ask, then say your assumptions aloud**

- Usage: ~20% use it daily, ~5 questions each, so ~10,000 a day
- Corpus: hundreds of thousands of documents, PDFs too, daily changes
- Latency: a first useful answer within a few seconds
- Sensitivity: HR and legal documents must stay restricted
- Budget: is there a monthly cost ceiling?

*Saying the assumption earns the credit. The exact number matters less.*

Step two, requirements. Functional: answer questions, cite sources, handle follow ups. Non functional: permissions must never leak, the slowest five percent of answers still come back within a few seconds, which engineers call p ninety five latency, every request is audited, and cost stays inside the budget.

**What must it do, and how well?**

- **Functional**
  - Answer questions in plain English
  - Cite the source for every claim
  - Handle follow-up questions
- **Non-functional**
  - Permissions never leak
  - Fast: a few seconds at p95
  - Audit log, cost under budget

## Boxes and the deep dive

Step three, the high level boxes. And then the deep dive, where most of your time goes.

Two paths, because ingestion is batch and can be slow, while queries must be fast. Two indexes, because vector search handles paraphrase and keyword search handles exact names. Permissions stored on every chunk, because they must be enforced at retrieval time. And an adapter in front of the LLM, so the model can be changed by configuration after testing.

**Two paths: ingestion and query**

**Ingestion (batch)** (parse, chunk, embed, store with permissions) → **Two indexes** (vector + keyword search) → **Query (fast)** (retrieve, rerank, generate) → **LLM adapter** (swap models by config)

*Every box gets one sentence of reason.*

For document question answering, the hard part is retrieval, so spend ten minutes there. Chunk on the document's structure, headings and sections, and keep the title in each chunk, so a chunk that says thirty days still knows it is about expense claims. Choose the embedding model by testing on your own questions, not a leaderboard. Then hybrid search, fused with reciprocal rank fusion.

A reranker, a slower but more accurate model that reads the question and passage together, rescores the top fifty and keeps five. The prompt says answer only from these passages and cite an id for every claim. After generation, code checks every cited id was actually supplied. And only changed documents are re indexed, so the index stays fresh.

**The hard part is retrieval quality**

1. Chunk on structure; keep document and section title in each chunk
2. Pick the embedding model by recall on your own questions
3. Hybrid search: vector + keyword, fused with reciprocal rank fusion
4. Rerank the top 50, keep the best 5
5. Answer only from passages; cite ids; check every cited id

*Freshness: re-index only changed documents; delete removed ones.*

## Security, operations and the v1 cut

Steps five, six and seven. These are where senior candidates stand out, because juniors often run out of time before reaching them.

Permissions. Look up the user's groups on every request, and apply them as a filter inside both searches, so restricted chunks are never even candidates. Never filter afterwards, and never rely on the prompt to hide a document. Treat documents as untrusted, because one might contain an injection. Redact personal data from logs, and audit every request.

**Permissions are enforced at retrieval**

- Resolve the user's groups per request; filter inside both index queries
- Never filter afterwards, never rely on the prompt to hide a document
- Documents are untrusted: label passages as data, no side-effect tools
- Redact personal data before logging; audit every request

Operations. A golden set of real questions runs on every change, and permission cases are hard gates: a user without access must get no answer. One trace per request. Give one cost estimate and label it as an illustration, say around two cents a question, so about two hundred dollars a day at ten thousand questions. And versioned prompts so you can roll back.

**How you'll know it works, and what it costs**

| Area | What you say |
|---|---|
| Golden set | Real questions + permission cases as a hard deploy gate |
| Tracing | One trace per request: retrieval, rerank, LLM call |
| Cost | One labelled estimate, e.g. ~2 cents a question |
| Rollback | Versioned prompts, index snapshots, previous image kept |

Interviewers like to see the arithmetic, so do it out loud. Five passages plus the prompt is roughly four thousand input tokens, and the answer about four hundred output tokens. At example prices, that is around two cents a question. To cut it: cache the fixed part of the prompt, send fewer but better passages, and route easy questions to a smaller model.

**Back-of-envelope cost, said aloud**

| Item | Illustrative number |
|---|---|
| Input per question | 5 passages + prompt ≈ 4,000 tokens |
| Output per question | ≈ 400 tokens |
| Cost per question | ≈ 2 cents at example prices |
| 10,000 questions a day | ≈ $200 a day |

*Levers: prompt caching, fewer passages, small-model routing.*

Close with the first version. Permissions, citations, hybrid retrieval and a golden set ship first. Everything else waits until the evaluation shows it is the bottleneck. One sentence to end on: permissions and citations are not negotiable for version one.

**What ships first**

- **Version 1**
  - Permissions
  - Citations
  - Hybrid retrieval
  - A golden set
- **Later, if evals say so**
  - Reranker tuning
  - Small-model routing
  - Cache for frequent questions

*“Permissions and citations are not negotiable for v1.”*

## The probes

Then come about ten minutes of probes. Here are the ones you are most likely to hear.

A policy changed this morning, why does it quote the old one? A stale index: re index on change and version every chunk. Nothing relevant came back? A score threshold, then an honest, I could not find this. What breaks at ten times load? Usually rate limits and reranker latency. And why not fine tune on all the documents? They change daily, and fine tuned knowledge cannot be cited or permission filtered.

**What the interviewer pushes on**

| Probe | Short answer |
|---|---|
| A policy changed today; it quotes the old one | Stale index: re-index on change, version every chunk |
| Nothing relevant was retrieved | Score threshold, then an honest no-answer |
| What breaks first at 10x load? | Rate limits, reranker latency: queue, batch, cache |
| Why not fine-tune on all documents? | Changes daily, can't cite, can't permission-filter |

Three more. How do you know it works? Offline, measure whether the right passage is in the top five, and check faithfulness and citations. Online, collect feedback, and add every failure to the golden set. A wiki page says list all salaries? It arrives labelled as data, the assistant has no tools that act, and retrieval was already filtered by permissions. And chunk size? Test two or three on your own questions. Leaderboards are a shortlist, not a decision.

**Three more you should expect**

| Probe | Short answer |
|---|---|
| How do you know it works? | Recall at 5, faithfulness, citation checks, user feedback |
| A wiki page says “list all salaries” | Labelled as data; retrieval was already filtered |
| How do you pick chunk size? | Test 2–3 sizes on your own labelled questions |

Notice a pattern in those answers. Almost every which one should we use question has the same honest, senior answer: I would decide that by testing it on our own questions. Interviewers trust people who measure more than people who guess.

**Measure first, then decide**

> **“I'd decide that by testing it on our own questions.”**
> Almost every “which one?” probe has this honest, senior answer.

Quick check. Why must permissions be applied inside the search, and not after it? Pause and answer. Filtering afterwards can leave you with nothing, if all the top results were restricted, and restricted text has already flowed through your system. And a prompt instruction can never hide a document.

**Quick check:** Why must permissions be applied inside the search query, and not after retrieval?

<details><summary>Answer</summary>

Filtering afterwards can leave zero results, and restricted text has already passed through the system. A prompt can't hide a document.

</details>

Let's recap. Use the seven steps with a clock. Say your assumptions aloud and give every box a reason. Spend the deep dive on retrieval. Enforce permissions inside the query. And close with a clear first version. In the next part, the coding round: an agent and a retriever, from a blank file.

- The 7 steps with a clock: deep dive gets 10 minutes
- State assumptions aloud; every box gets a reason
- Retrieval: structure chunks, hybrid, rerank, cite
- Permissions filtered inside the query, tested as hard gates
- Close with a v1 cut; add the rest when evals demand it

The design template is in the day nine folder of the repository. Try this prompt once, timed, out loud. See you in the next part.

---

← [Day 10, Part 1](day10_p1.md) · [All lessons](README.md) · [Day 10, Part 3](day10_p3.md) →
