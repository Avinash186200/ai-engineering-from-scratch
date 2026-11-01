"""How a real tokenizer cuts text into tokens.

Uses tiktoken (pip install tiktoken), a free, open tokenizer. It downloads its vocabulary
once. If tiktoken is missing or offline, a tiny BPE-style merge demo runs instead.
Run:  python day01_llm_basics/tokens_demo.py
"""
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")   # the rupee sign prints on any console

TEXTS = ["Which funds look best this week?",
         "Deccan Bond Fund returned 103.031",
         "Priya paid ₹1,250 via UPI"]


def tiktoken_demo():
    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")

    for text in ["Which funds look best this week?",
                 "Deccan Bond Fund returned 103.031",
                 "Priya paid ₹1,250 via UPI"]:
        ids = enc.encode(text)
        pieces = [enc.decode([i]) for i in ids]
        print(len(ids), pieces)


# ---- fallback: no download needed --------------------------------------------------------

def merge_once(words):
    pairs = Counter()
    for w in words:
        for a, b in zip(w, w[1:]):
            pairs[(a, b)] += 1
    if not pairs:
        return words, None
    best = pairs.most_common(1)[0][0]
    merged = []
    for w in words:
        out, i = [], 0
        while i < len(w):
            if i + 1 < len(w) and (w[i], w[i + 1]) == best:
                out.append(w[i] + w[i + 1])
                i += 2
            else:
                out.append(w[i])
                i += 1
        merged.append(out)
    return merged, best


def toy_bpe_demo(steps=12):
    """Learn merges from our three sentences, starting from characters."""
    words = [list(w) for t in TEXTS for w in t.split()]
    print("start:", sum(len(w) for w in words), "tokens (one per character)")
    for step in range(1, steps + 1):
        words, pair = merge_once(words)
        if pair is None:
            break
        print(f"merge {step}: {pair[0]!r}+{pair[1]!r} -> {sum(len(w) for w in words)} tokens")
    print("final pieces:", ["|".join(w) for w in words])


if __name__ == "__main__":
    try:
        tiktoken_demo()
    except Exception as exc:                  # not installed, or no network for the vocab
        print(f"(tiktoken unavailable: {type(exc).__name__}; showing a toy BPE instead)\n")
        toy_bpe_demo()
    print("rule of thumb: 1 English token ~ 4 characters; rupee signs and Hindi need more")
