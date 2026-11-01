"""A mini RAG pipeline: chunk, embed, keyword search (BM25), hybrid fusion, a prompt, and an eval.

Embeddings: sentence-transformers if installed, else a hashed bag-of-words fallback
(deterministic, no downloads). Run from the repo root:
    python day05_rag/mini_rag.py "What is an exit load?"              (prints the prompt)
    python day05_rag/mini_rag.py "What is an exit load?" --mode dense  (dense | keyword | hybrid)
    python day05_rag/mini_rag.py --eval                                (hit@3 per mode)
"""
from __future__ import annotations

import argparse
import hashlib
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np

DOCS = Path(__file__).with_name("docs")
MODES = ["dense", "keyword", "hybrid"]

EVAL_SET = [  # (question, file that should be retrieved, section title)
    ("What is NAV?", "fund_glossary.md", "NAV (net asset value)"),
    ("What fee do I pay if I sell units early?", "fund_glossary.md", "Exit load"),
    ("How does a SIP work?", "fund_glossary.md", "SIP (systematic investment plan)"),
    ("Is there a lock-in on tax-saving funds?", "fund_glossary.md", "ELSS (equity linked savings scheme)"),
    ("How is volatility measured?", "fund_glossary.md", "Volatility"),
    ("What is the exit load of Deccan Bond Fund?", "deccan_bond_factsheet.md", "Charges"),
    ("Expense ratio of Bharat Growth Fund", "bharat_growth_factsheet.md", "Charges"),
    ("How long should I hold a small cap fund?", "himalaya_small_cap_factsheet.md", "Overview"),
    ("Why are direct plans cheaper?", "fund_glossary.md", "Direct and regular plans"),
    ("What does AUM mean?", "fund_glossary.md", "AUM (assets under management)"),
]


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


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


def load_chunks(size=120, overlap=25) -> list[dict]:
    chunks = []
    for path in sorted(DOCS.glob("*.md")):
        chunks += chunk_text(path.read_text(encoding="utf-8"), path.name, size, overlap)
    return chunks


class HashedEmbedder:
    """Feature hashing into 512 dims: a cheap, download-free stand-in for a real embedder."""

    def __init__(self, dim: int = 512):
        self.dim = dim

    def encode(self, texts):
        out = np.zeros((len(texts), self.dim))
        for r, t in enumerate(texts):
            for tok in tokenize(t):
                h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
                out[r, h % self.dim] += 1 if (h >> 9) & 1 else -1
        return out


def get_embedder():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return HashedEmbedder()


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.toks = [tokenize(d) for d in docs]
        self.avg_len = sum(map(len, self.toks)) / len(self.toks)
        self.df = Counter(t for d in self.toks for t in set(d))
        self.n, self.k1, self.b = len(docs), k1, b

    def scores(self, query: str) -> np.ndarray:
        out = np.zeros(self.n)
        for q in tokenize(query):
            if q not in self.df:
                continue
            idf = math.log(1 + (self.n - self.df[q] + 0.5) / (self.df[q] + 0.5))
            for i, d in enumerate(self.toks):
                tf = d.count(q)
                out[i] += idf * tf * (self.k1 + 1) / (
                    tf + self.k1 * (1 - self.b + self.b * len(d) / self.avg_len))
        return out


class MiniRAG:
    def __init__(self, size=120, overlap=25):
        self.chunks = load_chunks(size, overlap)
        self.embedder = get_embedder()
        self.vectors = self.embed([c["text"] for c in self.chunks])
        self.bm25 = BM25([c["text"] for c in self.chunks])

    def embed(self, texts) -> np.ndarray:
        v = np.asarray(self.embedder.encode(list(texts)), dtype=float)
        norms = np.linalg.norm(v, axis=1, keepdims=True)
        return v / np.where(norms == 0, 1, norms)               # unit length

    def dense_search(self, query, k=3):
        # every row of self.vectors is a unit-length chunk embedding
        q = self.embed([query])[0]          # unit-length question vector
        scores = self.vectors @ q           # cosine similarity for ALL chunks
        top = np.argsort(-scores)[:k]       # best k, highest first
        return [(self.chunks[i], scores[i]) for i in top]

    def keyword_search(self, query, k=3):
        scores = self.bm25.scores(query)
        top = np.argsort(-scores)[:k]
        return [(self.chunks[i], scores[i]) for i in top]

    def hybrid_search(self, query, k=3, rrf_k=60):
        """Reciprocal rank fusion: add 1 / (60 + rank) from each ranking."""
        n = len(self.chunks)
        fused = np.zeros(n)
        for hits in (self.dense_search(query, n), self.keyword_search(query, n)):
            for rank, (chunk, _) in enumerate(hits):
                fused[self.chunks.index(chunk)] += 1 / (rrf_k + rank + 1)
        top = np.argsort(-fused)[:k]
        return [(self.chunks[i], fused[i]) for i in top]

    def search(self, query: str, k: int = 3, mode: str = "hybrid"):
        mode = {"bm25": "keyword"}.get(mode, mode)             # old name still works
        return {"dense": self.dense_search, "keyword": self.keyword_search,
                "hybrid": self.hybrid_search}[mode](query, k)


def build_prompt(question: str, hits) -> str:
    context = "\n\n".join(f"[{i}] ({c['source']} / {c['title']})\n{c['text']}"
                          for i, (c, _) in enumerate(hits, 1))
    return ("Answer the question using only the context below.\n"
            "Cite the bracket numbers you used.\n"
            "If the context does not contain the answer, say so.\n\n"
            f"CONTEXT:\n{context}\n\nQUESTION: {question}\nANSWER:")


def evaluate(rag: MiniRAG, k: int = 3):
    print(f"embedder: {type(rag.embedder).__name__}, chunks: {len(rag.chunks)}\n")
    print(f"Retrieval eval, hit@{k} per mode")
    for mode in MODES:
        misses = []
        for q, src, title in EVAL_SET:
            hits = rag.search(q, k, mode)
            if not any(c["source"] == src and c["title"] == title for c, _ in hits):
                misses.append(q)
        print(f"{mode:<8} hit@{k} = {len(EVAL_SET) - len(misses)}/{len(EVAL_SET)}")
        for q in misses:
            print(f"         miss: {q!r}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="What is an exit load?")
    ap.add_argument("--eval", action="store_true")
    ap.add_argument("--mode", default="hybrid", choices=MODES + ["bm25"])
    ap.add_argument("-k", type=int, default=3)
    ap.add_argument("--size", type=int, default=120, help="chunk size in words")
    ap.add_argument("--overlap", type=int, default=25)
    args = ap.parse_args()
    rag = MiniRAG(args.size, args.overlap)
    if args.eval:
        evaluate(rag, args.k)
    else:
        print(build_prompt(args.query, rag.search(args.query, args.k, args.mode)))
