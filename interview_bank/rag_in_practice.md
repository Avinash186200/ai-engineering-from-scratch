# RAG in practice

Code to back these answers: `day05_rag/mini_rag.py` (try `--mode` and `--size`). Worked design:
[`system_design/01_document_qa.md`](../system_design/01_document_qa.md).

### 1. Walk me through the document pipeline.
Ingest: parse files, clean, chunk, embed, store with metadata. Query: rewrite the question if needed, search
(vector plus keyword), rerank, put the top passages in the prompt with instructions to cite, generate, then check
the citations.

### 2. Why retrieval and not fine-tuning for documents?
Documents change, and users need sources. Retrieval updates by re-indexing and shows where each fact came from.
Fine-tuning bakes facts into weights, goes stale, and cannot cite.

### 3. Why retrieval for documents but tools for numbers?
Retrieval finds relevant text; it does not compute. A number like a forecast or a balance should come from the
system that owns it, through a tool, so it is exact and current.

### 4. How do you choose chunk size?
Start around 300-800 tokens with 10-15% overlap, split on headings and paragraphs, then tune on your eval set.
Small chunks retrieve precisely but lose context; large chunks keep context but dilute the match.

### 5. What goes wrong with PDFs?
Two-column layouts read in the wrong order, headers and footers repeated on every page, tables flattened into
noise, and scanned pages with no text layer. Use a layout-aware parser and inspect a sample of output.

### 6. RAG gives a wrong answer. How do you debug it?
Split the pipeline. Was the right passage in the corpus? Was it retrieved in the top k? Did it survive reranking?
Did the model use it? Each answer points to a different fix: parsing, chunking, search, or the prompt.

### 7. Why hybrid search and not just vectors?
Vectors are good at paraphrase and weak on exact codes, names and rare terms. Keyword search is the opposite.
Combining them, for example with reciprocal rank fusion, covers both.

### 8. What is reranking?
A second, slower model (a cross-encoder) reads the question and each candidate together and rescores them. You
retrieve 50 cheaply and keep the best 5. It is often the largest single quality gain.

### 9. How many chunks do you send to the model?
Enough to cover the answer, usually 3-8 after reranking. More adds cost and can bury the right passage.

### 10. What metadata do you store with each chunk?
Source id and title, section path, page, date or version, access groups, and language. It enables filters,
citations and permission checks.

### 11. How do you handle tables?
Extract them as structured rows or markdown with their headers, index each table (or row group) as its own chunk,
and keep a link to the page.

### 12. How do you keep the index current?
Track document hashes or a change feed, re-embed only what changed, and apply deletions and permission changes
first. Record an index version so you know what an answer was based on.

### 13. What if the answer is in no document?
The prompt allows "I couldn't find this in the documents", and you test that case. A guess is worse than a clear
"not found".

### 14. How do you show citations?
Number the passages in the prompt, ask the model to cite by number, then check in code that each cited number was
actually provided and map it back to a document link.

### 15. How do you evaluate retrieval separately from generation?
Retrieval: recall at k and MRR against labelled relevant passages. Generation: groundedness and correctness, from
checks or a calibrated judge. Measuring only the final answer hides which half failed.

### 16. How do you handle access control?
Store allowed groups on each chunk and filter inside the search query using the user's groups. Never filter
after retrieval, and test that one user cannot get another's documents.
