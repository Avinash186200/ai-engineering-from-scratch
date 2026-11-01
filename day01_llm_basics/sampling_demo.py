"""Temperature and top-p sampling, with real numbers.

Run:  python day01_llm_basics/sampling_demo.py
"""
import numpy as np

TOKENS = ["fund", "SIP", "NAV", "returns", "banana"]
LOGITS = np.array([3.0, 2.2, 1.8, 1.0, -1.0])


def softmax(logits, temperature=1.0):
    z = logits / max(temperature, 1e-6)
    z = z - z.max()
    p = np.exp(z)
    return p / p.sum()


def top_p_filter(probs, p=0.9):
    order = np.argsort(probs)[::-1]
    cum = np.cumsum(probs[order])
    keep = order[: int(np.searchsorted(cum, p) + 1)]
    out = np.zeros_like(probs)
    out[keep] = probs[keep]
    return out / out.sum()


def show(label, probs):
    print(f"{label:<22}" + "  ".join(f"{t}={q:.2f}" for t, q in zip(TOKENS, probs)))


if __name__ == "__main__":
    for t in [0.2, 0.7, 1.0, 1.5]:
        show(f"temperature={t}", softmax(LOGITS, t))
    show("T=1.0, top_p=0.9", top_p_filter(softmax(LOGITS, 1.0), 0.9))
    rng = np.random.default_rng(0)
    draws = rng.choice(TOKENS, size=1000, p=softmax(LOGITS, 1.0))
    print("1000 draws at T=1.0:", {t: int((draws == t).sum()) for t in TOKENS})
