# Interview questions: lessons learned

Each answer follows one pattern: **the challenge → what we changed → what improved → the honest limit**.
Say each one out loud in 30 to 45 seconds. The lessons are in [README.md](README.md).

---

### 1. Tell me about a result that was too good to be true.

**Challenge.** A backtest looked strong, and the long-horizon models added the most. They used a 2-day embargo on
labels up to 20 days long, so their training labels overlapped the return being predicted.
**What we changed.** Purge = horizon + embargo, a unit test for every horizon, and checks on the scores themselves.
**What improved.** The leak is now caught in CI, even though no feature looks ahead.
**Honest limit.** After the fix there was no reliable edge. I withdrew the old numbers.

### 2. What leakage mistakes have you made?

**Challenge.** In old projects I fitted the scaler, clusters and feature importance on all the data, and I used a
random 70/30 split on orders that happen in time.
**What we changed.** Fit on train only inside a pipeline, time-based splits, and a purge at the fold boundary.
**What improved.** Test results are no longer optimistic by construction.
**Honest limit.** I left those old repos as they were and wrote down what I would do differently, so readers can
see the before and after.

### 3. How do you catch a leak that a normal test misses?

**Challenge.** A truncation test passed on a same-date join that leaked, because nothing read a later row.
**What we changed.** A perturbation test: scramble every input not yet available at decision time and check the
feature does not move. Plus a run on pure noise.
**What improved.** In a breakage study, a same-bar mistake took IC from -0.055 to 0.782. The guard flags it.
**Honest limit.** It checks the features you give it. A label overlap needs checks on the scores.

### 4. How do you know your backtest is not just luck?

**Challenge.** We picked the best of 25 settings each month. The picks scored 1.35 in-sample and earned 0.36 the
next month.
**What we changed.** Walk-forward selection, a threshold chosen by nested walk-forward, a hold-out scored once,
and a deflated Sharpe with the true number of trials.
**What improved.** The naive 1.94 became an honest 1.27, and on noise the pipeline says "no edge".
**Honest limit.** A two-year hold-out is noisy; ours happened to be the best stretch.

### 5. Have you ever had to say "there is no signal"?

**Challenge.** After fixing a leak, a hedge overlay did not beat a constant short position.
**What we changed.** I said so, withdrew the figures, and published the corrected method on synthetic data.
**What improved.** Nobody built on a number that was not real.
**Honest limit.** It is an uncomfortable conversation, and it is still the right one.

### 6. Your RAG has good recall. Why are the answers wrong?

**Challenge.** Recall@5 was 0.898, exact match 0.195. An old duplicate page ranked first.
**What we changed.** A cross-encoder reranker.
**What improved.** MRR went from 0.573 to 0.964, and exact match reached the oracle-context score.
**Honest limit.** About 200 ms more per query on CPU, and the data was synthetic.

### 7. How do you stop an LLM from inventing numbers?

**Challenge.** "Only use numbers from tools" is a prompt, not a check.
**What we changed.** The model writes tokens instead of digits; code checks each token and renders the value.
**What improved.** Every number in an answer traces back to a tool result.
**Honest limit.** It proves where a number came from, not that the answer is relevant.

### 8. How did you pick your semantic cache threshold?

**Challenge.** At 0.80, the hit rate was 44.9%, but 6.6% of queries got a wrong answer.
**What we changed.** Start at 0.90, log near-misses, label them, add an entity check.
**What improved.** Zero false hits at 0.90, at a 20.7% hit rate.
**Honest limit.** Model calls were simulated; the shape transfers, not the exact numbers.

### 9. Tell me about a bug where the metrics looked fine.

**Challenge.** A LoRA run had val loss 0.006, but only 22% of test outputs were valid JSON.
**What we changed.** The max length cut every example before the closing brace. I raised it and added an
assertion that raises if any example would be truncated.
**What improved.** Validity went to 100%.
**Honest limit.** Low loss is not proof. I read the outputs now.

### 10. Can fine-tuning teach a model your company's facts?

**Challenge.** Teams want to "train the model on our data".
**What we changed.** I tested it: 30 values seen in training.
**What improved.** Clarity: 0 of 30 recalled, same as the base. Facts go in RAG; fine-tuning is for format.
**Honest limit.** One small model and one task. It matches what I would expect elsewhere, but I have not tested
every size.

### 11. A drift alert fires. Do you retrain?

**Challenge.** PSI jumped to about 1.0 and AUC did not move. Later a concept shift hurt AUC, and drift
monitoring could not see it.
**What we changed.** A promotion gate on AUC, calibration and schema, and scheduled retrains.
**What improved.** The gate rejected 11 of 17 retrains, and it blocked a model with an ECE of 0.214.
**Honest limit.** The shifts were planted and clean, and retraining was cheap.

### 12. How do you keep secrets out of a repo?

**Challenge.** A key was deleted from the code but still in an early commit.
**What we changed.** Rotated it first, published from clean history, and added a pre-push gate for secrets, names,
local paths and data files.
**What improved.** Nothing leaves the laptop without passing the gate, and I check real CI after every push.
**Honest limit.** A gate only finds patterns it knows. Rotation is the real fix.

### 13. Tell me about a hard bug to reproduce.

**Challenge.** A clean 401 arrived as a malformed chunked response on my laptop.
**What we changed.** Reproduced on a clean machine: the server was fine; antivirus software rewrote the response.
**What improved.** Now I reproduce on a clean machine first, and compute evidence in the production container.
**Honest limit.** It costs a few minutes per bug.

### 14. What do you check in a code review beyond the diff?

**Challenge.** I once approved a fix and missed the same bug in a sibling file.
**What we changed.** A checklist: sibling files, replies against code, dead switches, other open PRs, open
questions, every review note, CI green on the latest commit.
**What improved.** Fewer bugs came back after merge.
**Honest limit.** Slower reviews, and it does not replace tests.
