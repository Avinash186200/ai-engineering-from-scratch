# 1. Look-ahead and leakage audits

**Public repos:**
[vol-etp-hedge-overlay](https://github.com/Avinash186200/vol-etp-hedge-overlay),
[meta-labeling-trade-filter](https://github.com/Avinash186200/meta-labeling-trade-filter),
[feature-factory](https://github.com/Avinash186200/feature-factory),
[emerging-market-feature-library](https://github.com/Avinash186200/emerging-market-feature-library),
and two old repos, kept as they were, each with a "what I would do differently" section:
[ml-trading-classifiers-2020](https://github.com/Avinash186200/ml-trading-classifiers-2020),
[ecommerce-returns-ml-2021](https://github.com/Avinash186200/ecommerce-returns-ml-2021).

## The problem

A model that predicts the future must only see the past. Leakage is any feature, label or setting that uses
information from after the decision time. It makes a backtest look good and a live model look bad.

## What went wrong

These are real findings from my own audits, not textbook examples.

- **Label overlap (the big one).** An ensemble mixed models trained on horizons from T+1 to T+20, all with the
  same 2-day embargo. For a T+20 label, a row 3 days back contains the next ~17 days of returns, including the
  one being predicted. The long-horizon models were partly trained on the answer, and they were the members that
  "added the most". No feature looked ahead, so a feature-timestamp audit passed.
- **Scaler and friends fitted on all data.** In my 2020 work, standardisation, clustering and feature importance
  were fitted on the full history, test years included. In my 2021 work, the scaler for scoring was fitted on
  train and test together.
- **Random split on time series.** The 2021 return model used a random 70/30 split. Orders are in time and the
  history features use past returns, so the model saw the future.
- **Settings picked from the test year.** A trade filter's cutoff was taken from the test year's probabilities.
- **Fold boundary leak.** Training folds held trades entered before the test year but closed inside it: labels
  not yet known at decision time.
- **Same-bar and same-date joins.** Features stamped at the close of day t and paired with day t's return gave a
  correlation of **1.00** for the return feature. A foreign volatility index joined on the same date (it settles
  after the local close) leaked too, and the existing truncation test passed on that leaky join.

How big are these mistakes? The feature-factory breakage study made each one on purpose:

| Mistake | IC wrong | IC right |
|---|---|---|
| Same-bar data | 0.782 | -0.055 |
| Macro value on its reference date, not its release date | 0.221 | 0.002 |
| Centred 5-day window instead of trailing | 0.474 | 0.045 |

Noise turned into an "excellent" feature three times.

## The fix

- **Purge = horizon + embargo**, not a fixed small gap. A unit test checks that the last training label ends
  before the prediction row for every horizon, and another keeps the old leaky gap so the overlap stays visible.
- **Fit on train only, inside a pipeline**: scaler, clusters, importance, cutoffs.
- **Time-based splits**, walk-forward, with a purge at each fold boundary (a trade must exit before the test
  period starts).
- **A decision lag** on every generated feature, strict as-of joins for series from another calendar, and
  publication lags per column.
- **A perturbation test**: scramble every input not yet available at decision time and check the feature does
  not move. It catches same-day leaks that a truncation test misses.
- **Score-only diagnostics** for label overlap: IC by lead, and a refit-cycle fingerprint on the out-of-sample
  scores. They see a bug that no feature audit can.

After the purge, the overlay **showed no reliable edge on real data**. I withdrew the earlier headline figures.

## How to spot it next time

- The result is too good, or the members that "add the most" are the long-horizon ones.
- Any `fit` call that runs before the split. Any `shift(-k)`, `center=True` or full-sample statistic.
- A random split on anything with a date column.
- A threshold or cutoff chosen after looking at the test data.
- Run the pipeline on pure noise. A leak-free pipeline finds nothing there.

## Say it in an interview

> My backtest looked good, and the strongest models were the long-horizon ones. That was the warning sign.
> They used a 2-day embargo on a 20-day label, so training labels overlapped the answer.
> I set the purge to horizon plus embargo and added a test that fails if labels overlap.
> After the fix, the edge was gone, and I withdrew the old numbers.
> A feature audit could not find it, so now I also check the scores themselves.
