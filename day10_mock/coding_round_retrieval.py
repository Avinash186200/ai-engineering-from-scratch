"""Mock coding round: top-k cosine retrieval in pure numpy.

Bag-of-words vectors (crude but deterministic), normalised once, then one matrix multiply.
Watch for: zero vectors, normalisation, and argpartition for large corpora.
Run:  python day10_mock/coding_round_retrieval.py
"""
import re

import numpy as np

DOCS = [
    "NAV is the net asset value of one unit of a mutual fund.",
    "The expense ratio is the yearly fee a fund charges, as a share of assets.",
    "A SIP is a systematic investment plan that invests a fixed amount every month.",
    "Walk-forward validation trains on the past and tests on the next window.",
    "MCP is a protocol that lets an agent discover and call tools on a server.",
]
def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())
VOCAB = {w: i for i, w in enumerate(sorted({w for d in DOCS for w in tokenize(d)}))}
def embed(text):
    v = np.zeros(len(VOCAB))
    for w in tokenize(text):
        if w in VOCAB:
            v[VOCAB[w]] += 1.0
    return v


def normalise(m):
    norms = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(norms == 0, 1.0, norms)   # no divide-by-zero

D = normalise(np.stack([embed(d) for d in DOCS]))  # (5, |V|)

def search(query, k=1):
    q = normalise(embed(query))
    scores = D @ q                     # cosine = dot of unit vectors
    order = np.argsort(-scores)[:k]
    return [(int(i), round(float(scores[i]), 3)) for i in order]


def search_large(query, k=1):
    """Same result for big corpora: argpartition selects k in O(n), then sort only those k."""
    scores = D @ normalise(embed(query))
    k = min(k, len(scores))
    idx = np.argpartition(-scores, k - 1)[:k]
    idx = idx[np.argsort(-scores[idx])]
    return [(int(i), round(float(scores[i]), 3)) for i in idx]


if __name__ == "__main__":
    for q in ["what is the yearly fee", "monthly fixed investment plan", "quantum physics"]:
        print(f"Q: {q!r} -> {search(q, k=2)}")
        for i, s in search(q, k=1):
            print(f"   {s:.3f}  {DOCS[i]}")
    assert search("what is the yearly fee")[0][0] == 1
    assert search("quantum physics")[0][1] == 0.0          # unknown words: a safe zero score
    assert search_large("monthly fixed investment plan", 2) == search("monthly fixed investment plan", 2)
    print("tests passed")
