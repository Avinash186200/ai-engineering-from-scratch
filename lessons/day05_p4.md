# Day 5, Part 4: RAG Prompts, Citations and Evaluation (Recall@k, MRR, Faithfulness)

**Watch:** [youtu.be/CQHHOd-6Hmw](https://youtu.be/CQHHOd-6Hmw) · **Code:** [`day05_rag/`](../day05_rag/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

How do you know your RAG system actually works? This episode finishes Day 5: building a prompt with citations, measuring retrieval and answers, keeping documents secure and fresh, and deciding between RAG and a tool call.

## What you will learn

- How retrieved passages become a prompt the model can cite
- Retrieved text is data, not instructions (indirect prompt injection)
- Building a labelled question set; hit rate, recall@k and MRR worked by hand
- Faithfulness and LLM-as-judge, and how to calibrate a judge
- Access control and freshness in a real RAG system
- The routing rule: explain → RAG, rank → tool, why → both

## Chapters

- [0:00](https://youtu.be/CQHHOd-6Hmw?t=0) Intro
- [0:18](https://youtu.be/CQHHOd-6Hmw?t=18) Building the prompt with citations
- [2:52](https://youtu.be/CQHHOd-6Hmw?t=172) Evaluation: hit rate and MRR
- [5:41](https://youtu.be/CQHHOd-6Hmw?t=341) Faithfulness and LLM-as-judge
- [6:52](https://youtu.be/CQHHOd-6Hmw?t=412) Access control, freshness and routing

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In part three, we learned how to find the right chunks, with vector search, BM25, hybrid search and reranking. Now we put those chunks into a prompt, and learn how to prove the whole thing works.

## Building the prompt, with citations

Let's start with the prompt itself. The retrieved passages become part of what the model reads.

Here is the kind of prompt our script builds. Try it yourself with python day zero five rag slash mini rag dot py, followed by your question. Notice the first line: using only the context below. That tells the model to ground its answer in the passages, not its memory. And the third line gives it permission to say I don't know.

**What build_prompt produces**

`python day05_rag/mini_rag.py "What is an exit load?"`
```python
Answer the question using only the context below.
Cite the bracket numbers you used.
If the context does not contain the answer, say so.

CONTEXT:
[1] (fund_glossary.md / Exit load)
## Exit load  An exit load is a fee charged when you
redeem units before a set period ...

[2] (deccan_bond_factsheet.md / Charges)
## Charges  Exit load: 0.25% if redeemed within 30 days ...

[3] (fund_glossary.md / Expense ratio)
## Expense ratio  The yearly fee a fund charges ...

QUESTION: What is an exit load?
ANSWER:
```

Every element has a reason. Numbered passages with their source give the model something concrete to cite, and give us something to check. Permission to abstain matters: without it, models fill gaps from memory. And order matters: best passage first, only a few passages, and the question at the end, where models pay attention reliably.

**Why the prompt looks like this**

- “Using only the context” → answer from passages, not memory
- Numbered passages with source → something to cite and to check
- “If it's not there, say so” → permission to abstain
- Best passage first, few passages, question last

One security point, from day two. Treat retrieved text as data, never as instructions. If a document contains a line like, ignore previous instructions, it must not change the model's behaviour. That is called indirect prompt injection. Wrap passages in clear delimiters, and tell the model they are reference material only.

**Retrieved text is data, not instructions**

> **A document that says “ignore previous instructions” must change nothing.**
> Wrap passages in clear delimiters; say in the system prompt they are reference material. This is indirect prompt injection.

A citation can be wrong too. A cheap check in code: every citation number must point to a passage we actually sent. A stronger check: does that passage really support the sentence it is attached to? In our example, a good answer cites passage one, maybe two. Never three, which is about expense ratios.

**A citation is a claim too**

- Cheap check in code: every [n] must point to a passage we sent
- Stronger check: does passage [n] really support that sentence?
- A good answer to “What is an exit load?” cites [1], maybe [2], never [3]

You will hear a few advanced patterns in interviews. Query rewriting turns a vague follow up, like, and what about its lock in, into a clean search query. Multi query searches several phrasings. HyDE drafts a pretend answer and searches with that. Agentic RAG lets the agent decide when to search, and search again. Each one adds an extra model call, so add it only when your evaluation says you need it.

**Names interviewers will mention**

| Pattern | What it does |
|---|---|
| Query rewriting | LLM rewrites a vague follow-up into a clean search query |
| Multi-query | Search several phrasings, fuse the results |
| HyDE | Draft a pretend answer, search with that |
| Agentic RAG | The agent decides when and what to search, maybe again |

*Each adds an LLM call: add it only when evaluation shows you need it.*

## Evaluation: measuring retrieval

Which brings us to evaluation. You cannot tune what you do not measure.

RAG has two things to measure, and we keep them separate. Did retrieval find the right passages? And did the model use them faithfully? A perfect model on top of bad search still hallucinates. Perfect search with a careless model still gives wrong answers.

**Measure search and answer separately**

- **Retrieval**
  - Did we find the right passages?
  - Hit rate, recall@k, MRR
- **Generation**
  - Did the model use them faithfully?
  - Faithfulness, citation accuracy

*A perfect model over bad search still hallucinates.*

First, build a labelled set, also called a golden set. Start from real questions analysts ask. A person maps each one to the sections that answer it. Include the hard cases on purpose: fund codes, jargon, paraphrases, and questions the documents cannot answer. Label by section title, so it survives re-chunking. And grow it from every failure you find.

**Build a golden set of questions**

1. Start from real questions analysts actually ask
2. A person maps each question to the sections that answer it
3. Include hard cases: fund codes, jargon, paraphrases, unanswerable
4. Label by section title, so it survives re-chunking
5. Every wrong answer found in testing becomes a new case

Two metrics matter most. Hit at k: for what share of questions does at least one correct passage appear in the top k? And MRR, mean reciprocal rank. For each question, take one over the rank of the first correct passage. Rank one scores one, rank two scores a half. Then average. MRR rewards putting the answer right at the top.

**Hit rate and MRR**

- Hit@k: share of questions with a correct passage in the top k
- MRR: average of 1 / (rank of the first correct passage)
- Rank 1 → 1,  rank 2 → 0.5,  rank 4 → 0.25,  missing → 0
- Precision@k: share of the top k that is relevant (the noise you send)

Let's work one. Five questions, and the first correct passage lands at ranks one, two, one, four, and one. MRR is one plus a half plus one plus a quarter plus one, divided by five. Zero point seven five. Hit at three: four of the five are rank three or better, so eighty percent.

**Five questions, first-correct ranks**

1. Ranks: 1, 2, 1, 4, 1
2. MRR = (1 + 0.5 + 1 + 0.25 + 1) / 5 = 0.75
3. Hit@3: four of five ranks are 3 or better → 4/5 = 80%

*Metrics can disagree. Pick the one that matches how many passages you send.*

Run python day zero five rag slash mini rag dot py dash dash eval. It scores dense, keyword and hybrid on the labelled questions. Your numbers may differ from this illustration. And remember: with only ten questions, one question is ten percentage points. Treat the results as directions, not proof. Then try different chunk sizes and see what changes.

**Compare the three search modes**

```python
> python day05_rag/mini_rag.py --eval

Retrieval eval, hit@3 per mode
dense    hit@3 = 8/10
         miss: 'Is there a lock-in on tax-saving funds?'
keyword  hit@3 = 9/10
hybrid   hit@3 = 9/10
```

*Illustrative. With 10 questions, one question = 10 points. Directions, not proof.*

If you have done machine learning: this labelled set is your hold out set. Do not tune chunk size and fusion weights on the same ten questions you then report. You will overfit them. Keep a separate test portion.

**The same ideas you may already know**

> **The labelled set is your hold-out set.**
> Don't tune chunk size, k and weights on the same questions you report. Keep a separate test portion.

## Evaluation: measuring the answer

Now the second half: did the model use the passages faithfully?

Faithfulness, also called groundedness, asks: is every claim in the answer supported by the retrieved passages? Split the answer into claims and check each. Here, two claims are supported. The third, that exit loads pay for marketing, appears in no passage. Faithfulness is two out of three. And that unsupported claim is exactly the one we want to catch.

**Is every claim supported?**

| Claim in the answer | In a passage? |
|---|---|
| An exit load is a fee for redeeming early [1] | Yes |
| Deccan Bond Fund: 0.25% within 30 days [2] | Yes |
| It funds the fund's marketing costs | No |

*Faithfulness = 2 supported / 3 claims = 0.67*

Checking by hand does not scale, so teams use an LLM as judge: a second model call that grades each claim. But a judge is a model too, with its own biases, like favouring longer answers. So ask it narrow yes or no questions. Calibrate it against fifty to a hundred hand labelled examples before you trust it. And wherever plain code can check something, use code. Day six goes deep on this.

**LLM-as-judge, used carefully**

- A second model call grades each claim: SUPPORTED or NOT SUPPORTED
- Ask narrow yes/no questions, not a 1–10 score
- Calibrate: hand-label 50–100 examples, measure agreement first
- Use plain code checks where you can

## Security, freshness and routing

Three last topics turn a demo into a real product: permissions, freshness, and knowing when not to use RAG at all.

Not every user may see every document. The rule is strict: enforce permissions in the search, never in the prompt. Store access groups on every chunk. Take the user's permissions from their login session, not from anything typed in the chat. Filter inside the search. Never rely on a prompt saying, do not reveal this document, because anything in the prompt can be extracted. And test it with a restricted user.

**Permissions belong in the search**

1. Store access groups on every chunk at ingest
2. Get the user's permissions from the login session, never from the chat
3. Apply the filter inside the search
4. Never rely on “do not reveal document X” in the prompt
5. Test it with a restricted user

Documents change. A factsheet is updated every month. Give each document a stable id and a content hash, which is a fingerprint of its text. If the fingerprint is unchanged, skip it. If it changed, re-chunk, re-embed, and delete the old chunks together. Store each factsheet's effective date. And watch how long it takes for a change to become searchable.

**Documents change: index incrementally**

- Give each document a stable id and a content hash (a fingerprint)
- Unchanged hash → skip. Changed → re-chunk, re-embed, delete old chunks
- Store the factsheet's effective date on every chunk
- Monitor the lag between a change and it being searchable

Finally, the routing rule for our chatbot. Explain or define questions go to RAG, because the answer is written down. Rank, score or forecast questions go to the fund ranking tool, because no document holds today's number. And a why question uses both: the number from the tool, the meaning from the documents.

**RAG or tool?**

| Question | Route |
|---|---|
| What is an expense ratio? | RAG |
| Which funds rank highest this week? | Tool |
| Why is Bharat Growth Fund top, and what is its exit load? | Both |

*Explain → RAG. Rank or score → tool. Why → both.*

Here it is end to end. Rahul asks why Bharat Growth Fund is ranked first, and what its exit load is. The agent calls the ranking tool for the number. It retrieves the factsheet for the exit load. And the answer labels where each fact came from: the number from the tool, the exit load from passage two.

**One question, both routes**

> **User:** Why is Bharat Growth Fund ranked first, and what is its exit load?
>
> **Tool:** rank_funds: 1. Bharat Growth Fund, predicted +0.53%
>
> **Assistant:** The ranking model puts Bharat Growth Fund first, at +0.53% predicted (tool). Its exit load is 1% if redeemed within 1 year [2]. This is a research signal, not advice.

One honest caveat. The documents can explain what a term means. They cannot say how much something drove today's ranking. If Rahul wants that, it must come from a tool that reports the model's actual contributions. Never from the language model's own reasoning. And the numbers, as always, only from tools.

**Passages explain terms, not the model's reasons**

> **Documents say what a feature means, not how much it drove today's rank.**
> That must come from a tool that reports the model's contributions, never from the LLM's guess.

Last quick check. Four questions. The first correct passage is at rank one, rank one, rank two, and for the last one, it is not found at all. What is the MRR? Pause and work it out. The answer: one plus one plus a half plus zero, divided by four. Zero point six two five.

**Quick check:** First-correct ranks for four questions are 1, 1, 2, and not found. What is the MRR?

<details><summary>Answer</summary>

(1 + 1 + 0.5 + 0) / 4 = 0.625

</details>

Let's recap day five. Build the prompt with only the context, numbered passages, and permission to abstain. Retrieved text is data, never instructions. Measure retrieval and answers separately. Put permissions inside the search, and index incrementally. And route: explain to RAG, rank to a tool, why to both. Next, on day six, we build a proper evaluation harness, to test and monitor everything we have built.

- Prompt: “only the context”, numbered passages, permission to abstain
- Retrieved text is data, never instructions
- Measure retrieval (hit@k, MRR) and answers (faithfulness) separately
- Permissions go inside the search; index incrementally by hash
- Explain → RAG, rank → tool, why → both

The code is in the day zero five rag folder, linked in the description. Add your own document to the docs folder and see how it ranks. Subscribe, and I will see you on day six.

---

← [Day 5, Part 3](day05_p3.md) · [All lessons](README.md) · [Day 6, Part 1](day06_p1.md) →
