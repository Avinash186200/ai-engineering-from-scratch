# Day 9, Part 2: System Design: Document Q&A (RAG) for 10,000 Employees

**Watch:** [youtu.be/O_GfmqBscZ8](https://youtu.be/O_GfmqBscZ8) · **Code:** [`day09_design/`](../day09_design/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

A complete worked system design answer, said the way you would say it in an interview: a document question-and-answer system (RAG) for a 10,000-employee company, with permissions, estimates and the follow-up questions you should expect.

## What you will learn

- The clarifying questions to ask, and the assumptions to state
- Traffic, storage and token-cost estimates, with the arithmetic
- Structural chunking, hybrid search and reciprocal rank fusion
- Why permissions must be filtered inside the retrieval query
- Citation checks, the evaluation gate, and how to answer "what breaks at 10x?"

## Chapters

- [0:00](https://youtu.be/O_GfmqBscZ8?t=0) Intro
- [0:32](https://youtu.be/O_GfmqBscZ8?t=32) Clarify and requirements
- [2:14](https://youtu.be/O_GfmqBscZ8?t=134) The high-level boxes
- [3:27](https://youtu.be/O_GfmqBscZ8?t=207) Deep dive: retrieval and permissions
- [6:01](https://youtu.be/O_GfmqBscZ8?t=361) Security, operations, v1
- [7:38](https://youtu.be/O_GfmqBscZ8?t=458) The follow-up questions

## Lesson notes

Slide content and the full narration, in order.

Welcome back. Last time we learned the seven step method and five estimation formulas. Now we use them on a full design, said exactly the way you would say it in an interview.

The prompt: design a system that lets our ten thousand employees ask questions about internal documents. Every number you will hear is an assumption you state out loud. Prices are illustrative, not quotes.

**What the interviewer says**

> **“Design a system that lets our 10,000 employees ask questions about internal documents.”**
> All numbers here are assumptions you state. Prices are illustrative.

## Clarify and requirements

Step one. Do not draw anything yet. Ask.

Who uses it? Everyone, through a web app and the office chat tool. Which documents? About five lakh, across the wiki, SharePoint and Google Drive. Are there access rules? Yes, and the system must never reveal a document a user cannot open. First words in two seconds. Changes reflected within an hour. And a budget of a few thousand dollars a month.

**I ask, and I assume**

| I ask | Assumed answer |
|---|---|
| Who, and how? | All staff; web app plus Slack or Teams |
| Which documents? | Wiki, SharePoint, Drive: about 500,000 |
| Access rules? | Yes. Never show a document a user cannot open |
| Latency? | First words in 2 s; full answer in 8 s |
| Freshness, budget? | Changes live within an hour; a few thousand $ a month |

Functional requirements: answer with a citation for every claim, respect permissions, and handle follow ups. Non functional: zero permission leaks, and that is a rule, not a target. First words in two seconds at p ninety five, which means ninety five percent of requests are at least that fast. Freshness within an hour, and a full audit trail.

**What it does, and how well**

- **Functional**
  - Answer from documents, with citations
  - Respect permissions
  - Follow-up questions; thumbs up/down
- **Non-functional**
  - Zero permission leaks: absolute
  - p95 first token under ~2 s
  - Fresh within 1 hour; full audit

Now the numbers. Traffic, from last video, peaks at about one point six a second. Five lakh documents are about one point six billion tokens. Split into five hundred token pieces, that is three point two five million chunks, and about thirteen gigabytes of vectors: one database node. Each answer costs about two cents. So generation is the cost, and the design should send fewer, better chunks.

**The numbers, out loud**

| Quantity | Arithmetic |
|---|---|
| Traffic | 15,000 a day → peak ≈ 1.6 per second |
| Corpus | 500,000 docs × 3,250 tokens = 1.6 billion tokens |
| Chunks | ÷ 500 tokens each = 3.25 million chunks |
| Vectors | 3.25 M × 1,024 dims × 4 bytes ≈ 13 GB |
| Generation | 5,550 in + 300 out ≈ 2.1 cents a question |

*≈ $317 a day. Generation dominates cost, so cut input tokens.*

## The high-level boxes

Step three. Two paths: online, when someone asks, and offline, when documents change.

Online. First, a small model rewrites a follow up, like, and what about Bengaluru, into a full standalone question. Then we look up the user's groups, and search with those groups as a filter.

A reranker narrows fifty candidates to the best eight. The LLM answers only from those eight, citing each one. And then code, not the model, checks that every citation points to a passage we actually supplied.

**From question to cited answer**

**Rewrite** (follow-up → standalone question) → **Retrieve** (hybrid search, user's groups as filter) → **Rerank** (50 candidates → best 8) → **Generate** (answer only from the 8, with citations)

*Then code checks every citation points to a passage we supplied.*

Offline, connectors watch for changed documents, which are parsed, chunked and embedded, with the document's permissions stored on every chunk. A separate job keeps permissions in sync. Then I say: the deep dive I would choose is retrieval with permissions, because that is where quality and zero leakage both live. Where would you like me to go?

**Keeping the index fresh**

**Connectors** (wiki, SharePoint, Drive changes) → **Parse + chunk** (keep headings and tables) → **Embed + index** (text, vector, permissions, version) → **Permission sync** (every few minutes)

*Ask: “Where would you like me to go deep?”*

## Deep dive: retrieval and permissions

Step four, the deep dive. Four mechanisms: chunking, hybrid search, reranking, and permissions.

A chunk is the piece of text we store and search. Cutting every five hundred tokens slices tables in half. Better: split on headings, keep tables whole, and put the heading path at the start of each chunk. A chunk saying, the limit is five thousand rupees, is useless unless you know it is the hotel limit in the travel policy.

**Split by structure, not by size**

- **Every 500 tokens**
  - Cuts tables in half
  - Splits a procedure mid-step
  - “The limit is ₹5,000”: which limit?
- **By document structure**
  - Split on headings
  - Keep a table or list whole
  - Prefix: “Travel Policy > Domestic > Hotels”

Some people search exact words, like a form number. Others paraphrase, like, can I claim an Uber to the airport, when the policy says ground transport. Keyword search wins the first, vector search the second. Hybrid runs both, and merges them with reciprocal rank fusion: each list adds one over sixty plus the rank. Documents found by both rise to the top.

**Merge two lists with RRF**

| Document | Keyword rank | Vector rank | RRF score |
|---|---|---|---|
| Z | 2 | 1 | 1/62 + 1/61 = 0.0325 |
| X | 1 | 3 | 1/61 + 1/63 = 0.0323 |
| Y | – | 2 | 1/62 = 0.0161 |

*Found by both methods → rises to the top.*

A reranker is a model that reads the question and a passage together, and scores how relevant it is. Like a selector who watches a player bat, instead of just reading the scorecard. It is accurate but slow, so it only judges the top fifty. It costs a few hundred milliseconds, and saves tokens, because we send eight chunks instead of twenty.

**Cheap search first, careful reading second**

- A reranker reads the question and passage together
- Much more accurate, but too slow for millions of chunks
- So: retrieve 50 cheaply, rerank to the best 8

*Costs a few hundred ms. Saves input tokens: the biggest cost line.*

Permissions. Every chunk stores which groups may read its document. There are three places to enforce that. In the prompt: wrong, the text already reached the model. After retrieval: safe, but if forty five of fifty results are forbidden, the user gets five weak ones. Inside the search query: correct. Forbidden chunks are never even considered.

**Three places to enforce access**

| Where | What goes wrong |
|---|---|
| In the prompt | Text already reached the model: a prompt cannot hide it |
| After retrieval | Safe, but if 45 of 50 are forbidden, 5 weak results |
| Inside the query | Forbidden chunks never reach the model ✓ |

Two details that show you have built this. When someone leaves a group, that change must reach the index within minutes, and group lookup at query time should hit the live identity service. And if you cache answers, the cache key must include the user's permissions. Otherwise Priya's cached answer could be served to Rahul, who cannot see the sources.

**Permission traps**

- Sync lag: someone leaves a group → index updated in minutes
- Look up groups live at query time, not from a stale copy
- Cache key must include the permission set

## Security, operations, v1

Now the last three steps, quickly, three minutes each.

Security. Permissions, plus a nightly test where fake users try to retrieve restricted documents. Personal data: for HR files, log only ids. Prompt injection: a wiki page saying, ignore your instructions, is treated as data, and the system has no tools that act, so the worst case is a bad answer. Secrets stay out of prompts. And an audit trail of who saw what.

**Five items, fast**

- Permissions: pre-filter, plus a nightly probe-user test
- PII: tag HR collections; log ids, not text
- Injection: retrieved text is data; no tools that act
- Secrets in a secret manager, never in prompts
- Audit: user, chunks retrieved, prompt version, answer

Operations. A golden set of about two hundred real questions, with the expected source documents, must pass before any change ships. Online, watch thumbs, citation clicks, and the could not find rate per department: a spike usually means a connector broke. One trace per question. And a versioned index, so a bad rebuild is undone by switching back.

**How we know it works**

- Golden set: ~200 real questions + expected sources, gates every change
- Online: thumbs, citation clicks, “could not find” rate by department
- One trace per question: rewrite → retrieve → rerank → generate
- Versioned index: rebuild, test, switch an alias; roll back by switching back

And the close. The biggest trade-off is quality against latency. Version one is one connector, structural chunking, hybrid search with permission filtering, mandatory citations, and the golden set as a gate. Next come more connectors, the reranker if measurements show we need it, and caching and cheaper models once cost becomes the constraint.

**Close with three sentences**

> **v1: one connector, structural chunks, hybrid + permission filter, citations, a 200-question gate.**
> Next: more connectors; reranker if precision is weak; caching and model routing when cost bites.

## The follow-up questions

Then the interviewer probes. Here are the most common follow ups, with short answers.

What breaks first at ten times the load? Not our servers. Peak becomes about sixteen questions a second, roughly five and a half million tokens a minute, and the LLM provider's rate limit breaks first. Fix: negotiate limits, add a second provider behind the adapter, cache, and send fewer tokens.

**What breaks first at 10x the load?**

> **User:** What breaks first at 10 times the load?
>
> **Assistant:** Peak goes to ~16 questions a second, about 5.5 million tokens a minute. The provider's rate limit breaks first, not our servers. So: higher limits, a second provider behind the adapter, caching, and fewer input tokens.

Why not put everything into one long context model? One point six billion tokens fits in no context window. Even for smaller sets, you pay for every token, the model misses things buried in the middle, and permissions would live in the prompt, which is not enforcement.

**Why not one huge context window?**

> **User:** Why not put every document in a long-context model?
>
> **Assistant:** 1.6 billion tokens fits in no context window. Even for smaller sets, cost grows with every token sent, recall drops in the middle of long prompts, and permissions would live in the prompt, which is not enforcement.

Quick check. Pause and answer: why must permissions be applied inside the retrieval query, and not in the prompt? The answer: once text is in the prompt, it has reached the model, and an injection or a mistake can leak it. A pre filter means forbidden chunks are never retrieved at all.

**Quick check:** Why must permissions be applied inside the retrieval query, not in the prompt?

<details><summary>Answer</summary>

Text in the prompt has already reached the model; a prompt cannot hide a document. A pre-filter means forbidden chunks are never retrieved.

</details>

Let's recap. Clarify first. The estimates show cost lives in generation. Chunk by structure, use hybrid search, and rerank fifty to eight. Filter permissions inside the query. And gate every change on a golden set. Next video: two more designs. Our own research assistant chatbot, and a platform that serves agents to many companies.

- Clarify first: users, scale, latency, permissions, budget
- Estimates show generation dominates cost, not servers
- Structural chunks + hybrid search (RRF) + rerank 50 → 8
- Permissions filtered inside the query; cache key includes them
- Golden set as a gate; versioned index for rollback

The retrieval code from day five is in the repo, linked in the description. Subscribe, and I will see you in the next video.

---

← [Day 9, Part 1](day09_p1.md) · [All lessons](README.md) · [Day 9, Part 3](day09_p3.md) →
