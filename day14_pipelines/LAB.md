# Day 14 lab: data pipelines and point-in-time data

Standard library only (SQLite). Run from the repo root.

## Step 1: load twice
```bash
python day14_pipelines/pipeline.py
```
The second load adds 0 rows. That is **idempotency**: a job can be retried after a crash, or re-run for a backfill,
without creating duplicates. It comes from the natural primary key `(series, value_date, published_at)` plus
`ON CONFLICT DO NOTHING`, inside one transaction.
Try: remove `published_at` from the primary key. Now the revised value overwrites the first one (or fails), and history is lost.

## Step 2: ask "what did we know, and when?"
In the output, March 2024's value is unknown on 31 March and on 11 April, first known on 12 April, and revised a month later.
On 1 April, a model may only use **February's first estimate**. Anything else is look-ahead.

## Step 3: break it, then catch it
The demo deletes a month (a **GAP**) and then checks on a much later date with no new loads (**STALE**).
Both are caught by `quality_checks`. In production these run after every load and alert. Stale data is the silent killer:
the model still answers, confidently, from old inputs.

## Step 4: backfill
The demo reloads only the missing month. Because loading is idempotent, a backfill is just "run the same job for a past range".
Real-world warning: big backfills can overload a shared database. Run them in batches, off-peak, and watch the load.

## Step 5: see what leakage does
```bash
python day14_pipelines/leakage.py
```
Same data, same model. The naive join (today's revised numbers, including a month that was not yet published) gives R^2 about 0.69.
The point-in-time version gives about 0.12. The difference is pure fiction. This is how backtests and model evaluations lie.

## Step 6: SQL patterns
```bash
python day14_pipelines/sql_examples.py
```
As-of with `ROW_NUMBER()`, deduplication, gaps with `LAG()`, revision sizes, running averages and upserts.
These are the window-function questions data and AI interviews ask. Change the as-of date in query 1 and predict the result first.

## Step 7 (exercise): add a daily series
Add a daily price series with a one-day publication lag (today's close is available tomorrow morning).
Write `quality_checks` for it: a missing business day is a gap, a weekend is not.

## The checklist for any data feed
1. What period does each value describe, and when was it **published**?
2. Is it ever **revised**? Keep every version.
3. What is the natural key? Make loads **idempotent**.
4. How **fresh** must it be? Alert when it is late.
5. Every model input, training row and AI answer uses an **as-of** query.
