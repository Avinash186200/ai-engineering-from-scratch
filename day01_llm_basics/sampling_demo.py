"""Temperature (and top-p) sampling, with real numbers.

Run:  python day01_llm_basics/sampling_demo.py
"""
import numpy as np

tokens = ["Bharat", "Nifty", "Deccan", "a"]
scores = np.array([2.0, 1.5, 1.2, 0.5])

for T in [0.5, 1.0, 2.0]:
    p = np.exp(scores / T)
    p = p / p.sum()                      # softmax
    print(f"T={T}:", dict(zip(tokens, p.round(2).tolist())))


# ---- going further: top-p, and what sampling looks like over many draws ----------------

def softmax(logits, temperature=1.0):
    z = logits / max(temperature, 1e-6)
    z = z - z.max()                      # numerically safe
    p = np.exp(z)
    return p / p.sum()


def top_p_filter(probs, p=0.9):
    order = np.argsort(probs)[::-1]
    cum = np.cumsum(probs[order])
    keep = order[: int(np.searchsorted(cum, p) + 1)]
    out = np.zeros_like(probs)
    out[keep] = probs[keep]
    return out / out.sum()


if __name__ == "__main__":
    print("T=1.0, top_p=0.8:", dict(zip(tokens, top_p_filter(softmax(scores), 0.8).round(2).tolist())))
    rng = np.random.default_rng(0)
    draws = rng.choice(tokens, size=1000, p=softmax(scores, 1.0))
    print("1000 draws at T=1.0:", {t: int((draws == t).sum()) for t in tokens})
