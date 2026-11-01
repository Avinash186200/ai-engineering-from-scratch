"""A bigram next-word model: the smallest possible "language model".

It counts which word follows which, then predicts the next word from those counts.
Run:  python day01_llm_basics/next_token_toy.py
"""
import random
from collections import Counter, defaultdict

TEXT = """
a sip is a fixed monthly investment . a sip builds discipline .
a fund has a nav . the nav changes every day . the fund charges an expense ratio .
a low expense ratio helps returns . a high expense ratio hurts returns .
the market goes up . the market goes down . the fund follows the market .
"""


def train(text):
    words = text.split()
    counts = defaultdict(Counter)
    for prev, nxt in zip(words, words[1:]):
        counts[prev][nxt] += 1
    return counts


def next_word_probs(counts, word):
    c = counts[word]
    total = sum(c.values())
    return {w: n / total for w, n in c.most_common()}


def generate(counts, start, n=10, seed=7):
    rng = random.Random(seed)
    out = [start]
    for _ in range(n):
        probs = next_word_probs(counts, out[-1])
        if not probs:
            break
        out.append(rng.choices(list(probs), weights=list(probs.values()))[0])
    return " ".join(out)


if __name__ == "__main__":
    model = train(TEXT)
    for w in ["the", "expense", "market"]:
        probs = ", ".join(f"{k}={v:.2f}" for k, v in next_word_probs(model, w).items())
        print(f"after '{w}': {probs}")
    print("generated:", generate(model, "a"))
