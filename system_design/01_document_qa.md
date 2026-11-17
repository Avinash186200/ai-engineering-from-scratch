# Design 1: document Q&A for a 10,000-person company

**Prompt**: "Employees should be able to ask questions about internal documents (policies, wikis, handbooks,
engineering docs) and get answers with sources."

## 1. Clarify (assumed answers)

- Users: 10,000 employees, about 20% use it on a given day, 5 questions each: 10,000 questions a day.
- Corpus: 500,000 documents, mostly PDF, wiki pages and slides; about 5,000 change each day.
- Latency: first words in under 2 s, full answer in under 8 s.
- Sensitivity: documents have access rules (HR, legal, finance). A user must never see text they could not open.
- Budget: a few cents per question.

## 2. Requirements and estimates

- Functional: answer with citations, say "I don't know" when the documents do not cover it, respect permissions.
- Non-functional: permission correctness is non-negotiable; freshness within an hour; audit log of who asked what.
- Peak RPS: 10,000 / 86,400 x 10 = about 1.2. Small. The hard parts are retrieval quality and permissions, not load.
- Chunks: 500,000 docs x about 10 chunks = 5 M chunks. At 1,024 dims x 4 bytes, about 20 GB of vectors.

## 3. Boxes

```
User -> SSO -> API -> query rewriter -> hybrid retriever (vector + keyword, filtered by user groups)
                                     -> reranker -> prompt builder -> LLM (streamed) -> citation check -> user
Ingestion: connectors -> parse -> chunk -> embed -> index (with ACL metadata) ; change feed every few minutes
Traces + feedback -> eval store
```

## 4. Deep dive: retrieval and permissions

- **Chunk by structure**: split on headings and sections, 300-800 tokens with a small overlap; keep the title and
  section path in each chunk so it makes sense alone.
- **Hybrid search**: dense vectors catch paraphrases; keyword search (BM25) catches exact terms, codes and names.
  Merge with reciprocal rank fusion.
- **Rerank**: a cross-encoder scores the top 50 and keeps 5-8. Costs about 100-200 ms and usually lifts precision a lot.
- **Permissions inside the query**: each chunk stores the groups allowed to read it; the search filter uses the
  user's groups. Filtering after retrieval is wrong: it leaks through counts and returns empty results.
- **Grounded answer**: the prompt says to answer only from the passages and cite them; a post-check verifies each
  citation points to a retrieved chunk, and the answer is blocked or flagged if not.
- **Freshness**: a change feed re-indexes edited documents; deleted documents and changed permissions are applied
  first, since they matter for safety.

## 5. Data and security

SSO identity on every request; ACL metadata synced from the source systems; retrieved text treated as untrusted
(it may contain injected instructions); PII redaction in logs; audit log retained per policy.

## 6. Operations

Golden set of 200 real questions with expected source documents; track recall at k for retrieval and groundedness
for answers; a permission test suite (user A must never get document B) as a hard CI gate; cost and latency per stage.

## 7. Trade-offs and v1

- v1: two or three major sources, hybrid search, reranker, citations, permission filter. No conversation memory
  beyond the current thread.
- Later: more connectors, a semantic cache for frequent questions, query routing to a smaller model for simple lookups.
- Biggest trade-off: a reranker adds latency and cost but is the cheapest quality gain available.

## Likely probes

- "What if the answer is spread over five documents?" Raise k for that query type, or use a two-step plan:
  retrieve, summarise each, then answer.
- "How do you handle tables?" Extract tables as markdown or rows with their headers, and index them as separate chunks.
- "A user says an answer is wrong." Look up the trace: was the right chunk retrieved? If not, retrieval; if yes, generation.
