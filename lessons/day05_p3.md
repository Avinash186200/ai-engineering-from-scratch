# Day 5, Part 3: Vector Search, BM25 and Hybrid Search for RAG Explained

**Watch:** [youtu.be/dJnYNreGUKk](https://youtu.be/dJnYNreGUKk) · **Code:** [`day05_rag/`](../day05_rag/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

How does a RAG system actually find the right passage? This episode covers retrieval: vector search and indexes, BM25 keyword search worked by hand, hybrid search with reciprocal rank fusion, and rerankers.

## What you will learn

- Brute-force vector search, and when you need an index (IVF, HNSW)
- Vector stores: FAISS, Chroma, pgvector, Pinecone, and when each fits
- Why metadata filters must go inside the search, not after it
- The BM25 formula, with a score computed by hand
- Hybrid search: min-max fusion vs reciprocal rank fusion
- Bi-encoders vs cross-encoders, and where a reranker sits

## Chapters

- [0:00](https://youtu.be/dJnYNreGUKk?t=0) Intro
- [0:15](https://youtu.be/dJnYNreGUKk?t=15) Vector search and indexes
- [2:18](https://youtu.be/dJnYNreGUKk?t=138) BM25 keyword search
- [5:18](https://youtu.be/dJnYNreGUKk?t=318) Hybrid search and RRF
- [7:24](https://youtu.be/dJnYNreGUKk?t=444) Rerankers: bi-encoder vs cross-encoder

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In part two, we chunked our fund documents and turned each chunk into an embedding. Now comes the search itself: given a question, how do we find the right chunks?

## Vector search

We start with searching by meaning, which is called dense retrieval, because embeddings are dense lists of numbers.

With normalised vectors, exact search is one matrix multiplication. Every chunk gets a cosine score against the question, we sort, and take the top k. For thousands or even tens of thousands of chunks, this takes milliseconds. So do not add a vector database you do not need.

**Exact search is one line of NumPy**

`day05_rag/mini_rag.py`
```python
# every row of self.vectors is a unit-length chunk embedding
q = self.embed([query])[0]          # unit-length question vector
scores = self.vectors @ q           # cosine similarity for ALL chunks
top = np.argsort(-scores)[:k]       # best k, highest first
return [(self.chunks[i], scores[i]) for i in top]
```

*Thousands of chunks: milliseconds. Don't add a database you don't need.*

At millions of chunks, scanning everything gets slow. So we use approximate indexes. IVF groups vectors into clusters, and only searches the nearest few, like checking only nearby PIN codes. HNSW builds a layered graph, so search hops along highways first, then local streets. Both are much faster, but can occasionally miss a true neighbour.

**Approximate nearest neighbour indexes**

- **IVF**
  - Group vectors into clusters
  - Search only the nearest few
  - Like searching nearby PIN codes
- **HNSW**
  - A layered graph of neighbours
  - Hop from coarse to fine
  - Like highways, then local streets

*Much faster, but can miss a true neighbour. That miss rate is called recall.*

Here are the names you will hear. FAISS is a library that runs inside your own program. Chroma is a lightweight database, great for prototypes. Pgvector adds vectors to PostgreSQL, which is a natural fit if you already run Postgres: one database, with filters as ordinary SQL. And Pinecone is a fully managed service.

**Where vectors live**

| Product | What it is | Fits when |
|---|---|---|
| FAISS | A search library inside your app | You manage storage yourself |
| Chroma | A light open-source vector DB | Prototypes, small apps |
| pgvector | Vectors inside PostgreSQL | You already run Postgres |
| Pinecone | A managed, hosted service | You want no infrastructure |

Often a question must search only part of the corpus, say, only documents Priya's team may read. If you take the top five from everything and then filter, you might be left with zero, even though her answer sat at rank forty. And restricted text already passed through your system. Put the filter inside the search, so only allowed chunks ever compete.

**Filter inside the search, not after**

- **Post-filter**
  - Take top 5 from everything
  - Then drop what Priya can't see
  - Maybe 0 left, and restricted text was touched
- **Filter inside**
  - Only Priya's allowed chunks compete
  - Top 5 of those
  - Full recall, no exposure

## Keyword search: BM25

Dense search is powerful, but it has a blind spot. That is where good old keyword search comes in.

Dense search matches meaning, which is great when people paraphrase. But it blurs exact strings: fund codes, scheme names, identifiers. To an embedding, Nifty Value Fund and Nifty Value twenty Index may look almost identical. To an analyst, they are completely different products. Keyword search matches the exact words.

**Why keyword search still matters**

- Dense search matches meaning, which is great for paraphrases
- But it blurs exact strings: fund codes, scheme names, ISINs
- “Nifty Value Fund” and “Nifty Value 20 Index” may look alike to it
- Keyword search matches the exact words

BM25, short for best matching twenty five, is the standard keyword scoring method. It has four ideas. More mentions of a word means more relevant. But with diminishing returns: the tenth mention adds far less than the second. Long chunks get a discount, so they don't win just by being long. And rare words count a lot, while words like the count almost nothing. That last one is called IDF, inverse document frequency.

**Three ideas inside BM25**

1. Term frequency: more mentions of the word → more relevant
2. Saturation (k1 ≈ 1.5): the 10th mention adds far less than the 2nd
3. Length normalisation (b ≈ 0.75): long chunks don't win just by being long
4. IDF: rare words weigh a lot; words like “the” weigh almost nothing

Here is the formula. Don't panic, it is just those four ideas written down. For each query word, multiply its rarity, the IDF, by a term frequency part that flattens out, and that is discounted for long chunks. Add up over the words in the question.

**BM25, one term at a time**

```python
score(D, Q) = sum over each query word q of:

    IDF(q) * tf * (k1 + 1)
    -------------------------------------------
    tf + k1 * (1 - b + b * len(D) / avg_len)

IDF(q) = ln( 1 + (N - df + 0.5) / (df + 0.5) )

tf  = times q appears in chunk D
N   = number of chunks,  df = chunks containing q
```

Let's score one word by hand. Say our corpus has thirty two chunks, and the word exit appears in just one. Its IDF is the natural log of twenty two, about three point zero nine. The chunk mentions exit three times, and is a bit longer than average. Plug it in, and exit contributes four point nine. Compare the word the, which appears in twenty nine chunks: its IDF is about zero point one one. Almost nothing.

**Scoring “exit” for the exit-load chunk**

1. Corpus: N = 32 chunks; “exit” appears in df = 1
2. IDF = ln(1 + 31.5 / 1.5) = ln 22 = 3.09
3. The chunk says “exit” 3 times; it is 60 words, average is 50
4. Length part: 1.5 × (0.25 + 0.75 × 60/50) = 1.73
5. Score = 3.09 × 3 × 2.5 / (3 + 1.73) = 4.90

*“the” appears in 29 of 32 chunks: IDF ≈ 0.11, almost nothing.*

One trap to know. In a tiny corpus, IDF is noisy. If the word what appears in only one chunk, say a heading called What this fund invests in, then every question starting with what gets pulled towards it. The fixes: remove very common stopwords from keyword queries, or let a reranker clean up the top of the list.

**Stopwords can fool BM25**

> **In a tiny corpus, even “what” can look rare.**
> If “what” appears in only one heading, it scores like a real keyword. Fix: drop stopwords, or rerank.

If you have done some machine learning: BM25 is just TF-IDF with two corrections you might have added yourself. A capped transform on the counts, and a normalisation for document length.

**The same ideas you may already know**

> **BM25 is TF-IDF with two corrections.**
> A capped transform on word counts, and a normalisation for document length.

## Hybrid search: the best of both

Dense search understands meaning but blurs identifiers. Keyword search nails identifiers but misses synonyms. So why not use both?

Hybrid search runs both and combines the results. The difficulty: their scores are on totally different scales. Cosine sits between minus one and one. BM25 has no upper limit, and can easily reach fifteen. Just adding them would let keyword search drown out dense search.

**Scores live on different scales**

- **Dense (cosine)**
  - Between −1 and 1
  - Often 0.1 to 0.5 in practice
- **Keyword (BM25)**
  - No upper limit
  - Can be 0 to 15 or more

*Add them raw and BM25 drowns out dense.*

Fix one: min max normalisation. Rescale each score list to between zero and one, then take a weighted sum. It is simple, and our mini rag script uses it. But it has a weakness. If dense search has no real opinion, say its top three are almost a tie, normalisation stretches that noise into one, zero point nine seven, and zero point nine four, and it still votes at full force.

**Min–max normalisation**

- Rescale each list to 0–1: (x − min) / (max − min)
- Then a weighted sum, e.g. 0.5 × dense + 0.5 × keyword
- Weakness: dense scores 0.219, 0.213, 0.207 are a tie...
- ...but get stretched to 1.00, 0.97, 0.94 and vote at full force

Fix two: reciprocal rank fusion. Ignore the scores, use only the ranks. Each retriever gives a chunk a rank, and the fused score adds up one over sixty plus the rank. Sixty is a convention that softens the gap between first and second. A chunk both retrievers like beats a chunk only one of them loves. No calibration, no weights. That is why it is a robust default.

**Reciprocal rank fusion (RRF)**

| Chunk | Dense rank | Keyword rank | RRF score |
|---|---|---|---|
| Exit load | 1 | 1 | 1/61 + 1/61 = 0.0328 |
| Direct vs regular plan | 2 | 3 | 1/62 + 1/63 = 0.0320 |
| Expense ratio | 1 | 8 | 1/61 + 1/68 = 0.0311 |

*Uses only ranks. No calibration, no weights. A robust default.*

For those who know machine learning: hybrid search is ensembling. Min max is like averaging probabilities, RRF is like averaging ranks. And like any ensemble, it pays most when the two members make different mistakes.

**The same ideas you may already know**

> **Hybrid search is ensembling.**
> Min–max is like averaging probabilities; RRF is like averaging ranks. It pays most when the two make different mistakes.

## Reranking: a careful second look

The last stage of search is reranking. To understand it, we need two kinds of models.

Our embedding model is a bi encoder. It encodes the question and each passage separately, so passages can be embedded once, ahead of time. Fast. But the question and passage never actually see each other. A cross encoder reads them together, as one input, and gives one relevance score. Much more accurate, but it has to run once for every pair.

**Bi-encoder vs cross-encoder**

- **Bi-encoder**
  - Question and passage encoded separately
  - Passages embedded once, ahead of time
  - Fast, but they never “see” each other
- **Cross-encoder**
  - Reads question + passage together
  - Much more accurate
  - Must run once per pair: slow

So we use both, in sequence. Retrieval cheaply picks a shortlist of twenty to fifty. The cross encoder scores only those, and the best three to eight go to the model. It is like a recruiter: screen thousands of CVs quickly, then interview a shortlist properly. One warning. If the right chunk never made the shortlist, the reranker can never rescue it.

**Cheap shortlist, then careful scoring**

**Retrieve** (dense + BM25: top 20–50, cheap) → **Rerank** (cross-encoder scores only those) → **Send** (best 3–8 to the LLM)

*Like a recruiter screening CVs, then interviewing a shortlist.*

*If the right chunk isn't in the shortlist, the reranker never sees it.*

Quick check. Two retrievers rank a chunk second and third. With the constant sixty, what is its RRF score? Pause and work it out. The answer: one over sixty two, plus one over sixty three, which is about zero point zero three two.

**Quick check:** Two retrievers rank a chunk 2nd and 3rd. What is its RRF score with c=60?

<details><summary>Answer</summary>

1/62 + 1/63 ≈ 0.0161 + 0.0159 = 0.0320

</details>

Let's recap. Brute force vector search is fine up to tens of thousands of chunks. Indexes like HNSW trade a little recall for big speed. Filter inside the search. BM25 nails exact words, and hybrid search with RRF gets the best of both. Then rerank a shortlist. In the final part: building the prompt, citations, and measuring whether any of it works.

- Brute-force vector search is fine up to tens of thousands of chunks
- IVF and HNSW trade a little recall for big speed
- Filter inside the search, never after
- BM25 nails exact words; hybrid with RRF gets both
- Rerank a shortlist with a cross-encoder, then send the best few

Try python day zero five rag slash mini rag dot py with mode dense, keyword and hybrid, and compare. Subscribe, and see you in part four.

---

← [Day 5, Part 2](day05_p2.md) · [All lessons](README.md) · [Day 5, Part 4](day05_p4.md) →
