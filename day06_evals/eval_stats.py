"""Statistics for eval results: how sure can you be about a pass rate?

A golden set is a small sample. Before you block or ship a change on its score, ask two things:
  1. What range could the true pass rate be in?            -> wilson_interval
  2. Is version B really better than version A, or noise?   -> paired_compare (exact sign test)
  3. Does the gate hold when you count the uncertainty?      -> gate_decision

Run:  python day06_evals/eval_stats.py      (prints a worked example; standard library only)
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def wilson_interval(passed: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a pass rate. Better than p +/- 2*se for small n or p near 1."""
    if total <= 0:
        raise ValueError("total must be positive")
    if not 0 <= passed <= total:
        raise ValueError("passed must be between 0 and total")
    p = passed / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


@dataclass
class Comparison:
    only_a: int      # cases A passed and B failed
    only_b: int      # cases B passed and A failed
    p_value: float   # two-sided exact sign test on the disagreements

    @property
    def verdict(self) -> str:
        if self.p_value >= 0.05:
            return "no clear difference"
        return "B is better" if self.only_b > self.only_a else "A is better"


def paired_compare(a: list[bool], b: list[bool]) -> Comparison:
    """Compare two versions on the SAME cases. Only the cases where they disagree carry information."""
    if len(a) != len(b):
        raise ValueError("both versions must be run on the same cases")
    only_a = sum(1 for x, y in zip(a, b) if x and not y)
    only_b = sum(1 for x, y in zip(a, b) if y and not x)
    n = only_a + only_b
    if n == 0:
        return Comparison(0, 0, 1.0)
    k = min(only_a, only_b)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return Comparison(only_a, only_b, min(1.0, 2 * tail))


def gate_decision(passed: int, total: int, threshold: float = 0.90) -> str:
    """'pass' if even the low end clears the bar, 'fail' if even the high end misses it, else 'unsure'."""
    low, high = wilson_interval(passed, total)
    if low >= threshold:
        return "pass"
    if high < threshold:
        return "fail"
    return "unsure"


def _demo() -> None:
    for passed, total in [(10, 10), (45, 50), (180, 200)]:
        low, high = wilson_interval(passed, total)
        print(f"{passed}/{total} = {passed/total:.0%}  95% range {low:.0%}-{high:.0%}  gate@90%: "
              f"{gate_decision(passed, total)}")
    a = [True] * 40 + [False] * 10
    b = [True] * 38 + [False] * 2 + [True] * 8 + [False] * 2
    c = paired_compare(a, b)
    print(f"A {sum(a)}/50 vs B {sum(b)}/50: only A {c.only_a}, only B {c.only_b}, "
          f"p={c.p_value:.3f} -> {c.verdict}")
    assert wilson_interval(10, 10)[0] < 0.75, "10/10 must not look certain"
    print("Six points better on 50 cases is still within noise: add cases before you claim a win.")
    assert c.verdict == "no clear difference"


if __name__ == "__main__":
    _demo()
