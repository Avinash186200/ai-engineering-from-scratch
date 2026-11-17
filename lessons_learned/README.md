# Lessons learned: real mistakes from my own work

These are ten lessons from my own projects. Each one is a mistake I made, or a trap I caught, and what I changed.
They are not textbook examples. Where a public repo shows the work, the lesson links to it, and every number comes
from that repo's README, docs or results.

Each lesson has the same headings:

- **The problem**: what the work was trying to do.
- **What went wrong**: the real failure, with numbers where the repo has them.
- **The fix**: what changed.
- **How to spot it next time**: the warning signs.
- **Say it in an interview**: a 3-5 line spoken answer, following **challenge → what we changed → what improved
  → honest limit**.

Files in this folder:

- [CHEATSHEET.md](CHEATSHEET.md): all ten lessons on one page.
- [INTERVIEW_QA.md](INTERVIEW_QA.md): interview questions with spoken answers.

## The lessons

| # | Lesson | One line | Repo |
|---|---|---|---|
| 1 | [Look-ahead and leakage audits](01_leakage_audits.md) | A 2-day embargo on a 20-day label trained the model on the answer | vol-etp-hedge-overlay and others |
| 2 | [Honest evaluation](02_honest_evaluation.md) | Picks scored 1.35 in-sample and earned 0.36 next month | walk-forward-backtest-pipeline |
| 3 | [Architecture evolution](03_architecture_evolution.md) | The new agent loop lost to the old router, 69.6% vs 95.7% | arch_evolution/ |
| 4 | [Grounding and verification](04_grounding_verification.md) | Recall 0.898, exact match 0.195: order decided the answer | rag-evaluation-benchmark |
| 5 | [Measure, don't guess](05_measure_dont_guess.md) | A 0.80 cache threshold served 6.6% wrong answers | llm-serving-patterns |
| 6 | [Fine-tuning reality](06_finetuning_reality.md) | Val loss 0.006, valid JSON 22%: silent truncation | llm-finetuning-lora |
| 7 | [MLOps reality](07_mlops_reality.md) | PSI near 1.0, AUC unchanged; the gate rejected 11 of 17 retrains | mlops-model-lifecycle |
| 8 | [Shipping safely](08_shipping_safely.md) | A key deleted from the code was still in git history | day16_security/ |
| 9 | [Debugging production surprises](09_production_surprises.md) | Antivirus rewrote a 401; reproduce on a clean machine first | day13_cloud/ |
| 10 | [Reviewing code like a senior](10_reviewing_like_a_senior.md) | Same defect, sibling file; replies that do not match the code | day11_git_docker/ |

## The common thread

Most of these have one root: **a number I trusted without checking how it was made.** A backtest with a leak, an
in-sample score, a low loss, a drift alert, a green check I did not open. The fix is almost always the same habit:
measure the thing that matters, on data the system has not seen, in the environment where it will run.

## About the numbers

Lessons 1-2 and 4-7 use numbers from public repos. Most of those repos run on **synthetic data** with planted
structure, so anyone can reproduce them. The numbers show the mechanism and the direction of each effect, not its
size on real data. Where I found a problem in real-data work, I say what it was and do not publish the inflated
figures. Lessons 8-10 are habits from day-to-day engineering, so they have no benchmark numbers.
