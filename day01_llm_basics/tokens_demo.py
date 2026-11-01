"""How tokenizers split text: a tiny BPE-style merge illustration (no downloads).

Start from characters, then repeatedly merge the most frequent adjacent pair.
Run:  python day01_llm_basics/tokens_demo.py
"""
from collections import Counter

CORPUS = "fund funds fundamental refund nav navs expense expenses sip sips"


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


if __name__ == "__main__":
    words = [list(w) for w in CORPUS.split()]
    print("start:", sum(len(w) for w in words), "tokens")
    for step in range(1, 9):
        words, pair = merge_once(words)
        n = sum(len(w) for w in words)
        print(f"merge {step}: {pair[0]!r}+{pair[1]!r} -> {n} tokens")
    print("final split:", [" ".join(w) for w in words])
    print("rule of thumb: 1 English token ~ 4 characters; Hindi often needs more tokens per word")
