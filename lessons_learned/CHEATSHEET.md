# Cheat sheet: lessons learned

| # | Lesson | What went wrong | The fix | Warning sign |
|---|---|---|---|---|
| 1 | Leakage audits | 2-day embargo on a 20-day label; scaler fitted on all data; random split on time | Purge = horizon + embargo; fit on train only; time splits; perturbation test | Too good; long-horizon members "add the most" |
| 2 | Honest evaluation | Threshold tuned on the reported test; best-of-N shown as skill; `n_trials = 1` | Walk-forward, nested choice of settings, hold-out once, deflated Sharpe, noise test | In-sample shown, next period not |
| 3 | Architecture evolution | New agent loop lost to the old router | Keep the old one as a baseline; verify, bound, evaluate | No before/after on the same eval set |
| 4 | Grounding | High recall, wrong answers; prompt rule not enforced | Reranker; track MRR; code checks every number | Recall high, exact match low |
| 5 | Measure, don't guess | Loose cache threshold served wrong answers; router under-served | Strict threshold first; gate router on task success | A saving with no error rate next to it |
| 6 | Fine-tuning | Truncation: low loss, broken outputs; expected facts | Assert no truncation; read outputs; facts in RAG | Very low loss, bad outputs |
| 7 | MLOps | Drift alert with no harm; concept shift with no alert | Multi-metric promotion gate; scheduled retrains | Alert with no performance check |
| 8 | Shipping safely | Key in old history; env values printed by name filter | Rotate first; clean history; pre-push gate; check real CI | History has what the tip does not |
| 9 | Production surprises | Antivirus rewrote a 401; OS changed model output; timezone fell back to UTC | Clean machine first; evidence in the prod container; print resolved time | Bug on one machine only |
| 10 | Senior review | Same bug in a sibling file; reply did not match code | Checklist; approve only on green CI, no open blockers | Approval older than the latest commit |

## Numbers to remember (public repos, mostly synthetic data)

- Label leak: leaky T+20 model ranked first on no-signal data; after the purge, no reliable edge on real data.
- Breakage study IC, wrong vs right: same-bar 0.782 vs -0.055; macro on reference date 0.221 vs 0.002.
- Selection decay: 1.35 in-sample to 0.36 next month; on noise 1.22 to -0.35.
- Threshold choice: naive 1.94, nested walk-forward 1.27.
- FX engine on noise: walk-forward Sharpe -0.97, deflated Sharpe probability ~0.00.
- Reranker: MRR 0.573 to 0.964; exact match 0.195 to 0.488; ~200 ms per query on CPU.
- Cache: 0.80 threshold, 6.6% false hits; 0.90, zero false hits at 20.7% hit rate.
- Router: 28% cheaper, p50 4.80 s to 2.62 s, 15% under-served.
- Resilience: 65% to 94% with retries, 99.9% with breaker + fallback.
- LoRA truncation: val loss 0.006, valid JSON 22%; fixed, 100%. Facts recalled: 0 of 30.
- MLOps: PSI ~1.0 with no AUC change; gate rejected 11 of 17 retrains; ECE 0.214 blocked.

## The habits

1. Run it on noise. A sound pipeline finds nothing there.
2. Fit on train only. Split by time.
3. Count every trial. Report the next period, not the best.
4. Read the outputs, not just the loss.
5. Rotate a pushed key first; clean history second.
6. Reproduce on a clean machine; compute evidence where it will run.
7. Approve only on green CI for the latest commit, with no blocker open.
