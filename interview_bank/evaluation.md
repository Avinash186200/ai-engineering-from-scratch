# Evaluation

Code to back these answers: `day06_evals/eval_harness.py`, `day06_evals/eval_stats.py`.
Deep dive: [`day06_evals/DEEP_DIVE.md`](../day06_evals/DEEP_DIVE.md).

### 1. How do you know the AI gives good answers?
A golden set run in CI as a deploy gate, step-level metrics (tool choice, arguments, groundedness), a calibrated
judge for fuzzy qualities, a weekly human review sample, and user signals in production.

### 2. How would you detect hallucinations in production?
Check that numbers and citations in the answer match tool results and retrieved passages; run a groundedness judge
on a sample; watch user corrections and thumbs-down; review flagged traces and turn them into golden cases.

### 3. How does an ML background help here?
Train/test discipline, leakage awareness, metric choice, confidence intervals, and distrust of results that look too
good. The same habits apply to golden sets and prompt tuning.

### 4. What is LLM as judge, and what are the pitfalls?
Using a model to score outputs against a rubric. Pitfalls: position bias, preference for long answers and for its own
style, leniency on fluent errors. Calibrate it against human labels and swap answer order in pairwise comparisons.

### 5. How do you build a golden test set?
Real questions first, plus expert-written cases, past failures and attacks. Cover each intent and condition, record
expected tools and must-have facts, keep a holdout, and add a case for every production bug.

### 6. What metrics do you track?
Task success, tool selection accuracy, argument correctness, groundedness, refusal correctness, p50 and p95 latency,
and cost per completed task.

### 7. Version B scores 46/50 and version A 40/50. Ship B?
Not on that alone. Only the cases where they disagree matter; with 8 versus 2 a sign test gives p of about 0.11, so
it may be noise. Add cases or rerun before claiming B is better (`python day06_evals/eval_stats.py`).

### 8. How do you avoid overfitting the golden set?
Keep a holdout you never tune against, refresh with new real questions, and watch whether online signals move with
the offline score.
