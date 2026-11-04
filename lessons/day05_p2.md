# Day 5, Part 2: Chunking and Embeddings for RAG, Explained from Zero

**Watch:** [youtu.be/b0O11zsRPo8](https://youtu.be/b0O11zsRPo8) · **Code:** [`day05_rag/`](../day05_rag/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

How does a RAG system turn fund factsheets and a glossary into something a computer can search? This episode covers the ingest pipeline: loading, cleaning, chunking and embeddings, with a hand-worked cosine similarity example.

## What you will learn

- Why PDFs and tables are where RAG quietly breaks
- Metadata: the fields you must decide before indexing
- Four chunking strategies, overlap, and the chunk-size trade-off
- What an embedding is, and how embedding models are trained
- Cosine similarity worked by hand, and why we normalise vectors

## Chapters

- [0:00](https://youtu.be/b0O11zsRPo8?t=0) Intro
- [0:16](https://youtu.be/b0O11zsRPo8?t=16) Loading and cleaning
- [2:15](https://youtu.be/b0O11zsRPo8?t=135) Chunking strategies
- [5:10](https://youtu.be/b0O11zsRPo8?t=310) What an embedding is
- [7:12](https://youtu.be/b0O11zsRPo8?t=432) Cosine similarity by hand

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In part one, we saw why a chatbot needs RAG to answer from your own documents, and met its two pipelines. Now we build the first one: getting documents ready to be searched.

## Loading and cleaning documents

Retrieval can only find text that was extracted correctly. This step is unglamorous, and it is where many real systems quietly fail.

Most fund factsheets arrive as PDFs. A PDF is really a set of instructions for placing letters on a page. It has no idea what a paragraph is. So a two column factsheet often gets read straight across, mixing sentences from both columns.

Running headers and footers, like page three of twelve, or the standard mutual fund risk disclaimer, appear inside every page. After chunking, that noise sits in dozens of chunks.

Scanned pages are just pictures, so there is no text until you run OCR, optical character recognition, software that reads letters from images. And charts, like a fund's performance graph, simply disappear.

**PDFs are not really documents**

- Two columns get read across, mixing sentences
- Headers and footers repeat inside every page's text
- Scanned pages are images: no text until you run OCR
- Charts carry information that text extraction drops

Tables are the hardest case. A naive extractor turns a table into a stream of numbers with no column names. Nothing in it matches a question in words, and the model cannot tell which number is which. A better approach: turn each row into a sentence that carries its headers.

**Tables**

- **Naive extraction**
  - Bharat Growth 1.85 0.62 14.2 Deccan Bond 0.95 ...
  - Which number is which? Nobody knows
- **Better**
  - One sentence per row, with headers
  - “Bharat Growth Fund: expense ratio 1.85% (regular), 0.62% (direct)”

One more decision at this stage: metadata. That is structured information stored next to each chunk. Which file it came from, the section title, the date, the version, and who is allowed to read it. We use it later for filtering, citations and freshness. And you cannot filter on a field you never stored.

**Metadata**

> **Store source, section, date, version and access groups with every chunk.**
> You cannot filter on a field you did not store.

## Chunking

Next, chunking. Why cut documents into pieces at all?

Two reasons. First, we will turn each piece of text into a single list of numbers. Squeeze a twenty page factsheet into one list, and it becomes a blurry average that matches no specific question. Second, the prompt has a budget. We want to send the paragraph that answers the question, not the whole document.

**Why cut documents into pieces**

- One vector per text: a 20-page factsheet becomes a blurry average
- The prompt has a budget: send the paragraph, not the whole document

*A chunk is the unit you embed, retrieve and send.*

There are four common strategies. Fixed size: cut every N words, say every hundred and twenty. Simple, but it happily cuts in the middle of a sentence.

Structural: cut on headings and paragraphs. For a glossary, where each term has its own heading, this gives one chunk per definition. Very long sections still need a size cap.

Semantic: cut wherever the topic shifts, detected by comparing the meaning of neighbouring sentences. Useful for long prose with no headings, but it costs extra compute.

And parent child: search using small chunks, which match precisely, but send the model the whole parent section, so it has enough context. You get both, at the price of more plumbing.

**How to cut**

| Strategy | How it cuts | Risk |
|---|---|---|
| Fixed size | Every N words | Cuts mid-sentence |
| Structural | On headings and paragraphs | Long sections need a cap |
| Semantic | Where the topic shifts | Extra compute; tuning |
| Parent / child | Search small, return the big section | More plumbing |

With fixed size chunks, we usually add overlap. The next chunk repeats the last few words of the previous one. So if a boundary falls in the middle of a key sentence, like NAV is published once a day, after the market closes, the whole sentence survives in at least one chunk. The price is some duplicated text.

**Overlap keeps boundary sentences whole**

> Chunk 2 repeats the last few words of chunk 1:
`...units.` `NAV` `is` `published` `once` `a` `day` `|` `NAV` `is` `published` `once` `a` `day,` `after` `close.`

*Price: duplicated text in the index.*

Small chunks are precise, about one idea. But a small chunk might lose the term being defined, or the important caveat in the next sentence. Big chunks keep context, but blur several ideas together, and cost more tokens. There is no universal right size. You try a few, and measure, which we will learn in part four.

**Small chunks vs big chunks**

- **Small**
  - Precise: about one idea
  - May lose the term being defined
  - May lose the caveat next door
- **Big**
  - Keeps the context
  - Embedding blurs several ideas
  - Costs more prompt tokens

*No universal right size. Try a few and measure.*

Here is how our script does it. First a structural split, before every Markdown heading, so each glossary term becomes its own section. Then, only if a section is longer than a hundred and twenty words, a sliding window with an overlap of twenty five words. Each chunk keeps its source file and title as metadata.

**chunk_text in mini_rag.py**

`day05_rag/mini_rag.py`
```python
def chunk_text(text, source, size=120, overlap=25):
    chunks = []
    # 1. structural: split before every Markdown heading
    for section in re.split(r"\n(?=#+ )", text):
        title = section.strip().split("\n")[0].lstrip("# ")
        words = section.split()
        # 2. fixed size with overlap, only if a section is long
        step = size - overlap
        for start in range(0, max(len(words), 1), step):
            piece = " ".join(words[start:start + size])
            chunks.append({"source": source, "title": title,
                           "text": piece})
            if start + size >= len(words):
                break
    return chunks
```

## Embeddings: meaning as numbers

Now the heart of the ingest pipeline. How do we turn a chunk of text into something we can search by meaning?

An embedding model reads a piece of text and outputs a fixed length list of numbers, called a vector. It is trained so that texts with similar meanings produce vectors pointing in similar directions. So, how much do I pay the fund each year, lands close to the expense ratio chunk, even though they share almost no words.

**An embedding is a list of numbers**

- An embedding model reads text and outputs a fixed-length vector
- Similar meanings → vectors that point in similar directions
- “How much do I pay each year?” lands near the expense ratio chunk

The individual numbers mean nothing to a human. There is no fees coordinate. Think of map coordinates for Gurugram and Bengaluru. One number alone tells you little, but points that are close on the map are close in real life. Meaning lives in which vectors are near which.

**An embedding is a list of numbers**

> **Meaning lives in the geometry, not in any one number.**
> Like map coordinates: one number means nothing; nearby points are nearby places.

How are embedding models trained? With contrastive learning. Collect many matching pairs, like a question and the passage that answers it. Put a batch of, say, two hundred and fifty six pairs through the model. Each question must pick out its own passage from the batch. Pull the matching pairs together, push the others apart. The best models also add look alike wrong answers, so they learn fine distinctions, like direct plan versus regular plan.

**Contrastive learning, in plain words**

1. Collect matching pairs: a question and the passage that answers it
2. In a batch of 256 pairs, each question must pick its own passage
3. Pull matching pairs together, push the other 255 apart
4. Hard negatives: look-alike wrong answers teach fine distinctions

If you have done some machine learning before: this loss is ordinary softmax cross entropy, where the classes are the other passages in the batch. An embedding is a learned feature layer, and searching by embedding is just k nearest neighbours in that space. If not, don't worry, just keep going.

**The same ideas you may already know**

> **It is a softmax classifier where the classes are the passages in the batch.**
> An embedding is a learned feature layer. Dense search is k-nearest-neighbours in that space.

## Cosine similarity, worked by hand

So how do we measure whether two vectors point the same way? With cosine similarity. Let's do one by hand.

Here are toy vectors with just four numbers each. Real ones have hundreds. A question, what is an exit load? The exit load chunk. And the SIP chunk, which is about something else.

**Three vectors**

| Text | Vector |
|---|---|
| Question: “What is an exit load?” | q = [0.7, 0.6, 0.1, 0.1] |
| Chunk: Exit load definition | a = [0.8, 0.5, 0.3, 0.0] |
| Chunk: SIP definition | b = [0.2, 0.1, 0.1, 0.9] |

*Real embeddings have hundreds of numbers. Four is enough to see the idea.*

Multiply matching numbers and add them up. That is the dot product: zero point eight nine. Divide by the two lengths. We get zero point nine six four. For the SIP chunk, the same steps give only zero point three four five. One means the same direction, zero means unrelated. The exit load chunk clearly wins.

**cos(q, a) = (q · a) / (|q| × |a|)**

1. Dot product: q·a = 0.56 + 0.30 + 0.03 + 0 = 0.89
2. Lengths: |q| = 0.933, |a| = 0.990
3. cos(q, a) = 0.89 / (0.933 × 0.990) = 0.964
4. Same steps for SIP: cos(q, b) = 0.345

*1 = same direction, 0 = unrelated. The exit load chunk wins.*

Why cosine and not ordinary distance? Imagine a longer document whose vector points the same way, but is three times as long. Cosine stays at zero point nine six four. Straight line distance jumps from zero point two six to two point zero nine, so the longer document looks less relevant, even though it is about exactly the same thing.

**Direction, not length**

- **Cosine**
  - Compares direction only
  - A longer chunk on the same topic: still 0.964
- **Euclidean distance**
  - Sensitive to length
  - Same chunk, 3× longer: distance 0.26 → 2.09

So in practice we normalise: we scale every vector to length one. Then cosine similarity is just the dot product, and searching every chunk becomes a single matrix multiplication. Very fast.

**Normalise every vector to length 1**

> **Then cosine = a plain dot product.**
> Search over all chunks becomes one matrix multiplication.

Picking an embedding model? Public leaderboards give you a shortlist, but decide on your own questions, because finance jargon like ELSS or XIRR is exactly where general models are weakest. Watch memory: a million chunks of seven hundred and sixty eight numbers is about three gigabytes. And if you switch models, you must re-embed everything, because vectors from two models cannot be compared.

**Picking an embedding model**

- Use public leaderboards for a shortlist only
- Test on your own questions: jargon like ELSS, XIRR, exit load
- Weigh memory: 1 million chunks × 768 numbers × 4 bytes ≈ 3 GB
- Changing models means re-embedding everything

Quick check. Our glossary splits on headings first, and no section is longer than ninety words. Why might chunk sizes of a hundred and twenty and three hundred give exactly the same results? Pause and think. The answer: the size cap never triggers. The heading split already made one chunk per term.

**Quick check:** A glossary splits on headings, and no section is longer than 90 words. Why might chunk sizes 120 and 300 give identical results?

<details><summary>Answer</summary>

The size cap never triggers: the heading split already makes one chunk per term.

</details>

Let's recap. Bad extraction silently breaks retrieval. Store metadata with every chunk. Chunk structurally first, with a size cap and a small overlap. Embeddings put similar meanings close together. And normalised vectors make cosine a fast dot product. Next, we search: vector indexes, keyword search, and combining the two.

- Bad extraction (PDF columns, tables) silently breaks retrieval
- Store metadata with every chunk; you can only filter what you stored
- Chunk structurally first; add a size cap and small overlap
- Embeddings put similar meanings close together
- Normalise vectors: cosine becomes a fast dot product

The code is linked in the description. Run python day zero five rag slash mini rag dot py to try it. Subscribe, and see you in part three.

---

← [Day 5, Part 1](day05_p1.md) · [All lessons](README.md) · [Day 5, Part 3](day05_p3.md) →
