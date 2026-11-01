"""Mock coding round: top-k cosine retrieval in pure numpy.

Task: embed a few sentences (bag-of-words here), then return the k most similar to a query.
Watch for: zero vectors, normalisation, and argpartition for large corpora.
Run:  python day10_mock/coding_round_retrieval.py
"""
import re

import numpy as np

DOCS = [
    "NAV is the price of one unit of a mutual fund.",
    "The expense ratio is a yearly fee charged by the fund.",
    "An exit load is charged if you redeem units early.",
    "A SIP invests a fixed amount every month.",
    "Debt funds are less volatile than small cap funds.",
]


def tokenize(s):
    return re.findall(r"[a-z]+", s.lower())


def build_vocab(docs):
    return {w: i for i, w in enumerate(sorted({w for d in docs for w in tokenize(d)}))}


def embed(texts, vocab):
    m = np.zeros((len(texts), len(vocab)))
    for r, t in enumerate(texts):
        for w in tokenize(t):
            if w in vocab:
                m[r, vocab[w]] += 1
    return m


def cosine_top_k(query_vec, matrix, k=2):
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query_vec)
    sims = np.divide(matrix @ query_vec, norms, out=np.zeros(len(matrix)), where=norms > 0)
    k = min(k, len(sims))
    idx = np.argpartition(-sims, k - 1)[:k]          # O(n) selection, then sort just k
    idx = idx[np.argsort(-sims[idx])]
    return [(int(i), float(sims[i])) for i in idx]


if __name__ == "__main__":
    vocab = build_vocab(DOCS)
    M = embed(DOCS, vocab)
    for q in ["what fee do I pay to redeem early", "monthly fixed investment", "quantum physics"]:
        hits = cosine_top_k(embed([q], vocab)[0], M, k=2)
        print(f"Q: {q}")
        for i, s in hits:
            print(f"   {s:.3f}  {DOCS[i]}")
    assert cosine_top_k(np.zeros(len(vocab)), M, 2)[0][1] == 0.0   # zero query is safe
    print("tests passed")
