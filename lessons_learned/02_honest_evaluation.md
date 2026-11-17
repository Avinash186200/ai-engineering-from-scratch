# 2. Honest evaluation: when to say "no signal"

**Public repos:**
[walk-forward-backtest-pipeline](https://github.com/Avinash186200/walk-forward-backtest-pipeline),
[fx-strategy-backtester](https://github.com/Avinash186200/fx-strategy-backtester),
[feature-factory](https://github.com/Avinash186200/feature-factory).

## The problem

Try enough settings and one will look good by luck. The best of many noisy scores is too high by construction.
The question is not "what is the best result" but "how much of it came from choosing".

## What went wrong

- **The threshold was tuned on the test.** A selection threshold was swept on the same forward-test period that
  was reported, and the higher value was then recommended from that sweep. The forward test became in-sample.
- **Best of N, reported as skill.** Picking the best of 25 parameter sets each month: the picks scored an
  in-sample Sharpe of **1.35** and earned **0.36** the next month. On pure noise: **1.22** in-sample, **-0.35**
  the next month.
- **Deflated Sharpe with one trial.** A report computed the deflated Sharpe with `n_trials = 1` after a search
  over thousands of combos. Another counted only the final 7 configurations.
- **Naive significance.** With 34 candidate features, a plain p < 0.05 rule passed 10, and 5 of them were false.
- **Quiet months.** Zero-filled silent months and no minimum trade count let a set with 3 trades pass a Sharpe
  of 1.

## The fix

- **Walk-forward selection**: choose using only past months, trade only the next month, report only that.
- **Treat every setting as a hyper-parameter**: the threshold is chosen by nested walk-forward, and a final
  hold-out is scored once.

| How the threshold is chosen | Sharpe (synthetic data) |
|---|---|
| Naive: best on the whole forward test | 1.94 |
| Nested walk-forward | 1.27 |
| Hold-out, scored once on two years | 3.34 |

  The two-year hold-out happened to be the best stretch of the sample. The nested figure is the honest summary.
- **A selection-decay report** next to every result: in-sample score versus next-month result.
- **Deflated Sharpe with the true number of trials.**
- **Permutation tests that keep autocorrelation** (circular shift), plus **BH and family-wise control** for many
  candidates. The family-wise rule picked only true features (4 of 4) where the naive rule was half wrong.
- **A noise test in CI.** On a driftless random walk, the FX engine reports a walk-forward Sharpe of **-0.97**
  and a deflated Sharpe probability of about 0.00: "no edge, lose the costs". That is the right answer.

## How to spot it next time

- A setting was chosen on the period you report.
- The in-sample number is shown and the next-period number is not.
- `n_trials` is 1, or counts only the finalists.
- Nobody has run the pipeline on noise.
- Saying "no signal" feels like failure. It is a result, and it saves money.

## Say it in an interview

> We picked the best of 25 settings each month, and the picks looked great in-sample.
> I measured the next month: 1.35 dropped to 0.36, and on noise it went negative.
> So we chose the threshold by nested walk-forward, kept a hold-out, and counted every trial.
> The naive 1.94 became 1.27, which is the number I would defend.
> On pure noise the pipeline says "no edge", and that is why I trust it.
