"""A mini RAG pipeline: chunk, embed, BM25, hybrid fusion, and a hit@k eval.

Embeddings: sentence-transformers if installed, else a hashed bag-of-words fallback
(deterministic, no downloads). Run:
    python day05_rag/mini_rag.py "What is an exit load?"
    python day05_rag/mini_rag.py --eval
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

EVAL_SET = [  # (question, file that should be retrieved)
    ("What is NAV?", "glossary_basics.md"),
    ("What fee do I pay if I sell units early?", "glossary_costs.md"),
    ("How does a monthly SIP work?", "glossary_investing.md"),
    ("Which funds have a tax lock-in of three years?", "glossary_investing.md"),
    ("How is volatility measured?", "glossary_risk.md"),
    ("What is the exit load of Deccan Bond Fund?", "factsheet_deccan_bond.md"),
    ("Expense ratio of Bharat Growth Fund", "factsheet_bharat_growth.md"),
    ("How long should I hold a small cap fund?", "factsheet_himalaya_small_cap.md"),
    ("Why are direct plans cheaper?", "glossary_costs.md"),
    ("What does AUM mean?", "glossary_basics.md"),
]


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def chunk_docs(max_words: int = 60) -> list[dict]:
    """Split each doc on '## ' headings, then cap chunk size. Keep the title as context."""
    chunks = []
    for path in sorted(DOCS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ")
        for section in re.split(r"\n(?=## )", text):
            words = section.split()
            for i in range(0, len(words), max_words):
                body = " ".join(words[i:i + max_words])
                chunks.append({"source": path.name, "text": f"{title}: {body}"})
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
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.where(norms == 0, 1, norms)


def get_embedder():
    try:
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer("all-MiniLM-L6-v2")
        return type("ST", (), {"encode": lambda self, t: m.encode(t, normalize_embeddings=True)})()
    except Exception:
        return HashedEmbedder()


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.toks = [tokenize(d) for d in docs]
        self.avgdl = sum(map(len, self.toks)) / len(self.toks)
        self.df = Counter(t for d in self.toks for t in set(d))
        self.n, self.k1, self.b = len(docs), k1, b

    def scores(self, query: str) -> np.ndarray:
        out = np.zeros(self.n)
        for q in tokenize(query):
            if q not in self.df:
                continue
            idf = math.log(1 + (self.n - self.df[q] + 0.5) / (self.df[q] + 0.5))
            for i, d in enumerate(self.toks):
                f = d.count(q)
                out[i] += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / self.avgdl))
        return out


class MiniRAG:
    def __init__(self):
        self.chunks = chunk_docs()
        self.embedder = get_embedder()
        self.vecs = self.embedder.encode([c["text"] for c in self.chunks])
        self.bm25 = BM25([c["text"] for c in self.chunks])

    def search(self, query: str, k: int = 3, mode: str = "hybrid") -> list[dict]:
        dense = self.vecs @ self.embedder.encode([query])[0]
        sparse = self.bm25.scores(query)
        if mode == "dense":
            order = np.argsort(-dense)
        elif mode == "bm25":
            order = np.argsort(-sparse)
        else:  # reciprocal rank fusion of the two rankings
            rrf = np.zeros(len(self.chunks))
            for ranking in (np.argsort(-dense), np.argsort(-sparse)):
                for rank, idx in enumerate(ranking):
                    rrf[idx] += 1 / (60 + rank)
            order = np.argsort(-rrf)
        return [self.chunks[i] for i in order[:k]]


def evaluate(rag: MiniRAG, k: int = 3):
    print(f"embedder: {type(rag.embedder).__name__}, chunks: {len(rag.chunks)}")
    for mode in ["dense", "bm25", "hybrid"]:
        hits = sum(any(c["source"] == src for c in rag.search(q, k, mode)) for q, src in EVAL_SET)
        print(f"{mode:<7} hit@{k} = {hits}/{len(EVAL_SET)} = {hits / len(EVAL_SET):.0%}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="What is the exit load of Deccan Bond Fund?")
    ap.add_argument("--eval", action="store_true")
    ap.add_argument("-k", type=int, default=3)
    args = ap.parse_args()
    rag = MiniRAG()
    if args.eval:
        evaluate(rag, args.k)
    else:
        print(f"Q: {args.query}")
        for i, c in enumerate(rag.search(args.query, args.k), 1):
            print(f"{i}. [{c['source']}] {c['text'][:110]}...")
