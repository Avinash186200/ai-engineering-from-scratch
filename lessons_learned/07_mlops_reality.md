# 7. MLOps reality: drift alerts vs concept shift

**Public repo:** [mlops-model-lifecycle](https://github.com/Avinash186200/mlops-model-lifecycle).

## The problem

"Monitor drift, retrain when it fires" is the standard answer. Does a drift alert mean the model got worse? Does a
retrain make it better?

## What went wrong

- **A loud alert that did not matter.** PSI on one feature jumped from under 0.01 to about 1.0 when usage dropped
  40%. AUC did not move. Every candidate trained on the new data in the next five months failed the "beats
  production" gate.
- **A quiet change that did matter.** A concept shift (a cheaper rival plan changed what the features mean) took
  mean AUC from 0.804 to 0.780. Feature drift monitoring could not see it. The drift-triggered policy only caught
  it through the performance alert, four months late, because labels arrive a month late.
- **An AUC-only gate would have shipped a bad model.** One candidate had nearly the same AUC but an ECE of 0.214,
  because class weights inflated its probabilities.

## The fix

- A **promotion gate**: beat production AUC by at least 0.005, ECE at most 0.05, and the feed passes the schema
  check. Rollback in one call, all in an append-only audit log.
- Monthly retraining with the gate deciding: 17 training runs, and **the gate rejected 11** because they were no
  better. Mean AUC 0.815, the best of the three policies tested.
- Drift monitoring stays, to explain changes and catch broken feeds, not as the only trigger.

## How to spot it next time

- A drift alert with no performance check behind it.
- A gate that checks only one metric.
- Labels arrive late: count that delay in how fast you can react.
- Limit: the shifts here are planted and clean, and retraining takes seconds. With costly retrains the trade
  changes.

## Say it in an interview

> A feature drifted hard, PSI went to about 1.0, but AUC did not move.
> Then a concept shift hurt the model, and drift monitoring could not see it.
> We put a promotion gate on AUC, calibration and schema, and retrained on a schedule.
> The gate rejected 11 of 17 retrains, which stopped pointless releases.
> The data was synthetic with clean shifts; real drift is slower and messier.
