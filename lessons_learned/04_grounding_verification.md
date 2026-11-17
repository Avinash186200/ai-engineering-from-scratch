# 4. Grounding and verification

**Public repos:**
[rag-evaluation-benchmark](https://github.com/Avinash186200/rag-evaluation-benchmark), and the verifier in
this course: [arch_evolution/verifier_demo.py](../arch_evolution/verifier_demo.py).

## The problem

A RAG system can find the right passage and still give the wrong answer. A model told "only use numbers from
tools" can still type a number of its own.

## What went wrong

- **Recall looked fine, answers did not.** BM25 on section chunks had recall@5 of **0.898** but exact match of
  only **0.195**. A near-duplicate legacy page ranked above the current one, and the reader took the first.
  The right passage was in the top 5; it was not at the top.
- **The prompt rule was not enforced.** "Only use numbers from tools" is a request, not a check.

## The fix

- **A cross-encoder reranker.** BM25 MRR went from **0.573** to **0.964**, and exact match from 0.195 to 0.488,
  equal to the oracle-context score. After reranking, BM25, dense and hybrid all ended at 0.964. The price is
  about 200 ms per query on CPU, against under 10 ms without it.
- **Measure order, not just recall.** Track MRR and nDCG next to recall@k.
- **A deterministic verifier.** The model never types digits. Each number in a tool result gets a token; the
  answer uses tokens; code checks them with set lookups and renders the real values. A failed check gets at most
  two repairs, then the turn ends as `incomplete`, never as an unchecked answer.

## How to spot it next time

- Recall is high and answer quality is low: look at the ranking.
- Near-duplicate or outdated documents sit in the index.
- Answers contain numbers that nothing checks against the source.
- Limit: the verifier proves where a number came from, not that the answer is relevant.

## Say it in an interview

> Our retrieval had 0.898 recall, but the answers were often wrong.
> An old duplicate page ranked first, and the reader took it.
> We added a cross-encoder reranker, and MRR went from 0.573 to 0.964.
> For numbers, code checks every one against the tool output before the user sees it.
> The cost is about 200 ms per query, and the data was synthetic, so I would re-measure on real docs.
