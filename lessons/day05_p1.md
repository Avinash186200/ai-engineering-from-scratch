# Day 5, Part 1: What is RAG? Retrieval-Augmented Generation Explained Simply

**Watch:** [youtu.be/Lw681_Qo8RI](https://youtu.be/Lw681_Qo8RI) · **Code:** [`day05_rag/`](../day05_rag/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Why does a chatbot invent answers about your own documents, and how do real AI products fix it? This episode explains retrieval-augmented generation (RAG) from zero, using a research assistant chatbot that answers questions about Indian mutual funds.

## What you will learn

- The two places an LLM's knowledge comes from, and why there is no third
- Three ways to give a model your documents: stuff the prompt, fine-tune, or RAG
- The cost and quality maths of stuffing everything into the prompt
- When RAG is the wrong tool (live numbers, style, tiny documents)
- The two RAG pipelines, stage by stage, and how each one fails

## Chapters

- [0:00](https://youtu.be/Lw681_Qo8RI?t=0) Intro
- [0:25](https://youtu.be/Lw681_Qo8RI?t=25) Where we are in the series
- [0:48](https://youtu.be/Lw681_Qo8RI?t=48) The problem RAG solves
- [2:56](https://youtu.be/Lw681_Qo8RI?t=176) Stuffing vs fine-tuning vs RAG
- [6:30](https://youtu.be/Lw681_Qo8RI?t=390) The RAG pipeline, stage by stage

## Lesson notes

Slide content and the full narration, in order.

Hi, I'm Avinash, and welcome to day five of AI Engineering from Scratch. Today we teach our chatbot to answer from your own documents, using a technique called RAG. No machine learning background needed.

As always, if the pace feels slow, watch at one point two five times speed.

Here is where we are. We have seen how language models work, how to prompt them safely, how agents call tools, and how MCP plugs those tools into any AI. Today, day five, is about documents. After this, we learn to test and monitor what we build.

## The problem RAG solves

Let's start with the problem. Why can't the model simply answer questions about our documents?

A language model knows things from exactly two places. The first is its weights, everything it absorbed during training. That knowledge is frozen at a date called the knowledge cutoff. Think of a textbook it read years ago and cannot reopen.

The second is its prompt, the text you send in this call. Like notes you hand it right now. And there is no third source. The model cannot go and look anything up on its own.

**An LLM has only two sources**

- **1. Its weights**
  - What it absorbed in training
  - Frozen at its knowledge cutoff
  - Like a textbook it read years ago
- **2. Its prompt**
  - The text you send in this call
  - Fresh every time
  - Like notes handed to it right now

*There is no third source. It cannot look anything up by itself.*

So imagine Priya, an analyst, asks our chatbot: what is the exit load on Deccan Bond Fund? An exit load is a small fee you pay if you sell a fund too early. The model has never seen this fund's factsheet. So it guesses, fluently and confidently.

**Ask about your own documents**

> **User:** What is the exit load on Deccan Bond Fund?
>
> **Assistant:** Deccan Bond Fund charges a 2% exit load if redeemed within 3 years.

That is a hallucination. The real factsheet says zero point two five percent, only within thirty days. The model had no way to know. The only fix is to put the right text into the prompt.

**Ask about your own documents**

> **A confident guess is a hallucination.**
> The real factsheet says 0.25% within 30 days. The model never saw it.

That is exactly what RAG does. The name has three parts. Retrieval: at question time, a search step finds the few passages in your documents that are relevant.

Augmented: the prompt is extended with those passages. Like a student allowed to bring the right page of notes into an open book exam.

And generation: the model writes the answer from those passages, and cites them. The search finds the text. The model reads and explains it. Your whole collection of documents is called the corpus.

**Retrieval-augmented generation**

**Retrieve** (search your documents for the few relevant passages) → **Augment** (paste them into the prompt) → **Generate** (the LLM writes the answer and cites them)

*The search finds the text. The LLM reads and explains it.*

## Three ways to give a model your knowledge

Now, RAG is not the only option. Interviewers love asking you to compare three approaches, so let's learn the reasons, not just the verdict.

Option one: stuff the prompt. Just paste every factsheet and every glossary page into every single question. Simple, nothing to build. But it gets expensive fast, and soon it stops fitting.

Option two: fine tune. That means training the model a bit more on your documents. It sounds right, but it mainly teaches behaviour and style, not reliable facts. And every time a factsheet changes, you need another training run.

Option three is RAG. Search first, then send only the top few passages. It works at any size, it is cheap, you update it by re-indexing instead of retraining, it can cite sources, and it can respect who is allowed to see what. Its weakness: the search can miss, so we must measure it.

**Three ways to give a model your knowledge**

| Option | How it works | Main problem |
|---|---|---|
| Stuff the prompt | Send every document, every time | Costly; stops fitting |
| Fine-tune | Train the model further on your docs | Learns style, not facts |
| RAG | Search, then send the top few passages | Search can miss; must be measured |

*RAG: any corpus size, cheap, fresh, citable, permission-aware.*

Let's put numbers on it. Say our fund notes are two hundred pages, about one and a half lakh tokens. Remember, a token is a small word piece. And say the model charges two hundred and fifty rupees per million input tokens. Real prices vary; this is just for the maths.

If we stuff everything, each question sends one and a half lakh tokens. That is about thirty seven rupees fifty per question. At a thousand questions a day, that is thirty seven thousand rupees, every day, before the model writes a word.

With RAG, we send five passages of about three hundred tokens each. Fifteen hundred tokens, about thirty seven paise. One hundredth of the cost. And when the corpus grows ten times bigger, the RAG cost stays the same, because we still send five passages.

**Stuffing vs RAG, in rupees**

1. Corpus: 200 pages of fund notes ≈ 1,50,000 tokens
2. Say input costs ₹250 per million tokens (illustrative)
3. Stuffing: 1,50,000 tokens per question ≈ ₹37.50
4. RAG: 5 passages × 300 tokens = 1,500 tokens ≈ 37 paise

*One hundredth of the cost. And it stays flat as documents grow.*

There is also a quality argument. Models use information at the start and end of a long prompt more reliably than information buried in the middle. This is called lost in the middle. If the answer is one paragraph among six hundred, it is a needle in a haystack. RAG finds the needle first.

**Long prompts hurt answers too**

> **Lost in the middle**
> Models use the start and end of a long prompt better than the middle. RAG sends a short, focused prompt.

RAG is not always the answer. If the answer must be computed, or is live, no document contains it. Which funds rank highest today? That comes from our fund ranking model, a tool, like we built on day three.

If what you need is a style or a format, like every answer must look like a short research note, that is a job for prompting, not retrieval.

And if your documents are tiny, say a three page glossary that rarely changes, just put it in the system prompt. Retrieval adds a new way to fail, so use it only when it earns its place.

**When RAG is the wrong tool**

- The answer is computed or live: “Which funds rank highest today?” → call a tool
- The need is style or format: “always answer like a research note” → prompting
- The documents are tiny and rarely change → put them in the system prompt

*Retrieval adds a way to fail. Use it only when it earns its place.*

## The two pipelines of a RAG system

Now let's open up a RAG system and look at its parts. There are two pipelines.

The first is the ingest pipeline. It runs ahead of time, whenever documents change. Load the files. Clean them. Cut them into small passages called chunks. Then turn each chunk into a list of numbers, called an embedding, and store it. Think of a librarian cataloguing new books before anyone asks for them.

**Prepare the documents once**

**Load** (read PDFs, Word, Markdown) → **Clean** (strip noise, keep headings) → **Chunk** (cut into small passages) → **Embed + store** (turn into vectors, save with metadata)

The second is the query pipeline. It runs on every question. Retrieve the top few chunks. Optionally rerank them, meaning re-order the shortlist more carefully. Build a prompt with numbered passages. And let the model generate an answer with citations.

**Answer each question**

**Retrieve** (find the top few chunks) → **Rerank** (re-order the shortlist) → **Build prompt** (numbered passages + question) → **Generate** (answer with citations)

Every stage can fail on its own. Loading can turn a table into a soup of numbers. Chunking can cut a definition in half. The embedding may not understand jargon like ELSS. Retrieval may put the right chunk seventh when we only send five. And generation can add facts that were never in the passages.

**Each stage has a job and a failure**

| Stage | Typical failure |
|---|---|
| Load | Tables turn into a soup of numbers |
| Chunk | A definition is cut in half |
| Embed | Jargon like “ELSS” is not understood |
| Retrieve | The right chunk is 7th when we send 5 |
| Generate | Adds facts that are not in the passages |

So here is the most useful debugging rule in RAG. When an answer is wrong, first ask: was the right chunk retrieved at all? If not, no prompt can fix it. Most RAG failures in real products are search failures that look like model failures.

**Debug from the front**

> **Was the right chunk retrieved at all?**
> If not, no prompt can fix it. Most RAG failures are search failures that look like model failures.

In the code for today, the corpus lives in the day zero five rag docs folder. There is a glossary of fund terms like NAV, expense ratio, and SIP, plus factsheets for funds like Bharat Growth Fund and Deccan Bond Fund. Notice the headings. They will matter a lot in the next part.

**The documents we will search**

`day05_rag/docs/fund_glossary.md`
```python
## NAV (net asset value)
NAV is the price of one unit of a mutual fund. It is the
value of everything the fund owns, minus what it owes,
divided by the number of units. NAV is published once a
day, after the market closes.

## Expense ratio
The expense ratio is the yearly fee a fund charges, as a
percentage of your investment. A 1% expense ratio on
Rs 1,00,000 costs about Rs 1,000 a year.

## SIP (systematic investment plan)
A SIP invests a fixed amount every month, like Rs 5,000
on the 5th, through an auto-debit or UPI mandate.
```

Quick check. Pause and think. Rahul asks: which fund has the best predicted return this week? Should our chatbot use RAG? The answer: no. That number is computed and live. It comes from the fund ranking tool. RAG is for things that are written down.

**Quick check:** Rahul asks: “Which fund has the best predicted return this week?” Should the chatbot use RAG?

<details><summary>Answer</summary>

No. The answer is computed and live, so it comes from the fund-ranking tool. RAG is for what is written down.

</details>

Let's recap. A model knows only its weights and its prompt. RAG retrieves passages, adds them to the prompt, and then generates. It is cheaper and more accurate than stuffing, and better for facts than fine tuning. Live numbers go to tools. And there are two pipelines. In the next part, we build the first one: chunking, and turning text into numbers.

- An LLM knows only its weights and its prompt
- RAG retrieves passages, adds them to the prompt, then generates
- Cheaper and more accurate than stuffing; better for facts than fine-tuning
- Live numbers go to tools; tiny static docs go in the prompt
- Two pipelines: ingest ahead of time, query on every question

The code is linked in the description. If this helped, subscribe, and I will see you in part two.

---

← [Day 4, Part 4](day04_p4.md) · [All lessons](README.md) · [Day 5, Part 2](day05_p2.md) →
