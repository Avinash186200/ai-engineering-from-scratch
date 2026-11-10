# Interview questions: Data pipelines and point-in-time data

For each question: open **Understand it** and read until it is clear, then say the **Answer** out loud in 30-45 seconds.
Code for the ideas is in this folder; the hands-on steps are in [LAB.md](LAB.md).


## Pipeline basics

### 1. Walk me through a data pipeline you'd build to feed an AI or ML system.

<details><summary>Understand it</summary>

```text
THE STAGES
1. Extract: pull from sources (vendor APIs, SFTP files, databases, web pages, PDFs). Respect rate limits; keep the raw response.
2. Land raw: store exactly what arrived (object storage or a raw table), with the time you received it. Never lose the original; you will need to re-process.
3. Validate: schema, types, ranges, duplicates, completeness. Reject or quarantine bad batches instead of loading them silently.
4. Transform: clean, convert units, join reference data, compute features. Keep transformations in code (SQL/dbt/Python) under version control.
5. Load: into the serving store (Postgres, warehouse, feature store, vector store) idempotently.
6. Serve: models, dashboards and AI tools read through as-of queries.
7. Orchestrate and monitor: a scheduler (cron, Airflow, Dagster, Prefect, Cloud Scheduler) runs it; freshness, row counts and check results are monitored and alerted.

DESIGN PRINCIPLES
- Idempotent steps (safe to retry/backfill).
- Point-in-time correctness (store when data was published).
- Raw data immutable; derived data reproducible from raw + code.
- Small, testable steps with clear contracts between them.

FOR AI SPECIFICALLY
Documents for RAG flow through the same idea: extract, chunk, embed, index, with versioning so you know which document version an answer came from.
```

</details>

**Answer:** Extract from the sources and land the raw responses unchanged with a received timestamp, so I can always reprocess. Then validate schema, ranges, duplicates and completeness, and quarantine bad batches instead of loading them silently. Transform in version-controlled SQL or Python, and load idempotently into the serving store, recording when each value was published. Models and AI tools read through as-of queries, and a scheduler runs it all with freshness and quality monitoring. The same pattern feeds RAG: extract, chunk, embed, index, with document versions.

### 2. What does idempotent mean, and why does it matter in pipelines?

<details><summary>Understand it</summary>

```text
DEFINITION
Running an operation once or many times gives the same result. Load the same batch twice -> no duplicates, no double counting.

WHY IT MATTERS
- Jobs fail halfway and get retried (network errors, timeouts, preemptions).
- Schedulers sometimes run a job twice.
- Backfills re-run old date ranges on purpose.
- Without idempotency every retry is a risk, so people stop retrying and data stays broken.

HOW
1. A natural key that identifies a fact (series + value_date + published_at), with a unique constraint.
2. Upsert: INSERT ... ON CONFLICT DO NOTHING / DO UPDATE, or MERGE in warehouses.
3. Or overwrite a whole partition: delete date = X then insert date = X, in one transaction.
4. Transactions so a batch is all-or-nothing.
5. Deterministic transforms (no 'now()' baked into values, no random order dependence).
6. Record runs (run_id, rows seen, rows new) for auditing.

DAY 14 LAB
First load: 72 rows new. Same load again: 0 new.
```

</details>

**Answer:** Idempotent means running it once or ten times gives the same result. It matters because jobs fail halfway and get retried, schedulers double-fire, and backfills deliberately re-run old ranges; without it every retry risks duplicates. I get it with a natural key and a unique constraint plus upserts, or by overwriting a whole partition inside one transaction, and by keeping transforms deterministic. In my lab, the first load adds 72 rows and an identical second load adds zero.

### 3. Batch vs streaming: when would you use each?

<details><summary>Understand it</summary>

```text
BATCH
Process data in chunks on a schedule (hourly, nightly). Simple, cheap, easy to backfill and debug. Fits: daily market data, nightly model scoring, document re-indexing, reports.

STREAMING
Process each event as it arrives (Kafka, Pub/Sub, Kinesis + Flink/Spark Streaming/Beam). Low latency, more complex: ordering, late events, exactly-once semantics, state. Fits: fraud detection, live pricing, real-time personalisation, monitoring.

MICRO-BATCH
Small batches every few seconds or minutes. A middle ground.

DECISION
Ask: how fresh must the result be for the business decision? If daily is fine, batch. Many teams over-build streaming.
For an AI assistant answering analysts with daily data: batch ingestion, plus precomputed model scores, is right.
```

</details>

**Answer:** Batch processes data on a schedule; it's simple, cheap and easy to backfill, and fits daily market data, nightly scoring and re-indexing documents. Streaming processes events as they arrive with tools like Kafka or Pub/Sub; it gives low latency but brings ordering, late events and state to manage, and fits fraud detection or live pricing. I decide by how fresh the result must be for the decision. If daily is enough, batch. For an analyst assistant on daily data, batch ingestion with precomputed scores is the right call.


## Point-in-time

### 4. What is point-in-time correctness, and what is look-ahead bias?

<details><summary>Understand it</summary>

```text
THE IDEA
For any past date D, your system must be able to answer: 'what did we know on D?' Not what we know now about D.

WHY THE DIFFERENCE EXISTS
1. Publication lag: March's figure is published on 12 April. On 31 March, it doesn't exist yet.
2. Revisions: the first estimate is later revised. On 12 April you had the first estimate; today you have the revised one.
3. Late corrections, restatements, survivorship (delisted securities disappear from today's lists).

LOOK-AHEAD BIAS
Using information in training or a backtest that wasn't available at that time. The model 'sees the future'. Results look great and vanish in production.

DAY 14 LAB
Same model, same data. Naive join (today's revised data): R^2 about 0.69. Point-in-time: about 0.12. The gap is fiction.

HOW TO PREVENT
Store published_at for every value; train and evaluate with as-of queries; lag features to when they're truly available; keep delisted entities; review every join for time-travel.
```

</details>

**Answer:** Point-in-time correctness means for any past date I can reconstruct exactly what was known that day, not what we know now. The two differ because data is published late, gets revised, and entities disappear. Look-ahead bias is using information in training or a backtest that wasn't available yet, so results look great and vanish live. In my lab, the same model scores R-squared 0.69 with a naive join on today's revised data and 0.12 point-in-time. I prevent it by storing the publication date of every value and using as-of queries everywhere.

### 5. What is a bitemporal table? How do you design one?

<details><summary>Understand it</summary>

```text
TWO TIME AXES
- Valid time (value_date): the period the fact describes. 'Inflation for March 2024.'
- Transaction/knowledge time (published_at, and ingested_at): when the fact became known (to the world / to us).

DESIGN
Columns: entity/series, value_date, published_at, value, vintage, ingested_at.
Primary key: (series, value_date, published_at). A revision is a NEW row, not an update. History is never overwritten.

QUERIES
- As known on D: the latest row per value_date with published_at <= D (ROW_NUMBER() OVER (PARTITION BY value_date ORDER BY published_at DESC) = 1).
- Latest truth: the latest row per value_date regardless of date.
- Latest available on D for a model: the most recent value_date with published_at <= D.

WHY BOTH published_at AND ingested_at
published_at = when the world knew (for correctness). ingested_at = when we loaded it (for debugging, and a fallback when the source gives no publication time). If you only have ingested_at, use it conservatively: it's never earlier than the true publication.
```

</details>

**Answer:** A bitemporal table records two times for each fact: the period it describes and when it became known. Every revision is a new row keyed by series, value date and publication date, so history is never overwritten. An as-of query then takes, for each period, the latest row published on or before the date I'm asking about. I also keep ingested-at, when our pipeline loaded it, for debugging and as a conservative fallback when the source doesn't give a publication time.

### 6. How do point-in-time issues affect an LLM assistant, not just a model?

<details><summary>Understand it</summary>

```text
WHERE IT BITES
1. Tool results: 'what was the top fund on 2025-06-19?' must use data as of that date, not today's revised data.
2. RAG documents: a document published later than the question date shouldn't be used to answer 'what did we know then?'; also old and new versions of a policy can both be retrieved.
3. Evaluations: a golden-set answer computed with revised data marks correct historical answers as wrong.
4. Freshness: the assistant answers from stale data without saying so.

DESIGN
- Every tool takes an as_of parameter and returns the as-of date it actually used.
- Documents carry published/effective dates; retrieval filters by date when the question is historical.
- Answers show the as-of date: 'As of 2025-06-19, ...'.
- Freshness monitoring with alerts (Day 12).
- The model is told to state the as-of date and not to project beyond the data.
```

</details>

**Answer:** An assistant has the same risks. Its tools must answer historical questions with data as of that date, and RAG must not use documents published after the date in question, or mix old and new versions of a policy. Eval answers computed on revised data can mark correct historical answers wrong. So every tool takes an as-of parameter and returns the date it actually used, documents carry publication dates for filtering, answers state their as-of date, and data freshness is monitored with alerts.


## Data quality

### 7. What data quality checks would you run, and what do you do when one fails?

<details><summary>Understand it</summary>

```text
THE CHECKS
- Freshness: latest data date / publication date vs expected schedule. The most important one in finance.
- Completeness: expected rows present? Gaps in dates? Null rate per column?
- Uniqueness: duplicate keys.
- Validity: types, ranges (a yield of 4000%?), allowed categories.
- Consistency: totals match, foreign keys exist, units consistent.
- Distribution: sudden shifts in mean/variance vs history (a vendor changed units from % to decimal).
- Time travel: values published before their period ended.

WHEN ONE FAILS
1. Don't load silently. Quarantine the batch; keep serving the last good data, clearly marked with its as-of date.
2. Alert the owner with the failing check and sample rows.
3. Downstream: models/tools refuse or caveat instead of using bad inputs.
4. Fix at source or in transform; re-run idempotently; backfill.
5. Add a test for the new failure type.

TOOLS
Great Expectations, Soda, dbt tests, Pandera, or plain SQL checks like day14_pipelines.quality_checks.
```

</details>

**Answer:** Freshness first, then completeness and gaps, uniqueness of keys, validity of types and ranges, consistency across tables, distribution shifts that reveal unit changes, and time-travel, meaning values published before their period ended. When a check fails I don't load silently: I quarantine the batch, keep serving the last good data marked with its as-of date, alert the owner with sample rows, make downstream models caveat or refuse, fix and re-run idempotently, and add a test for that failure. Tools like dbt tests or Great Expectations, or plain SQL.

### 8. A vendor feed silently stopped updating. How would you detect it, and how do you limit damage?

<details><summary>Understand it</summary>

```text
DETECT
- Freshness check per feed: last value date and last publication/ingest time vs the expected schedule (business-day aware). Alert when late.
- Row count per load vs typical (a load of 0 rows is a failure, not a success).
- 'Flat line' check: identical values day after day for a series that normally moves.
- Downstream: model inputs' as-of dates in every prediction log.

LIMIT DAMAGE
- Models and tools check input freshness and refuse or caveat ('data as of 3 days ago').
- Answers display the as-of date so users notice.
- A fallback source if available, with reconciliation.
- Runbook: who contacts the vendor, how to backfill when it resumes.

AFTER
Backfill the missing period idempotently; re-run affected model outputs; tell users which outputs were affected.
```

</details>

**Answer:** I'd have a freshness check per feed comparing the last value date and load time against the expected business-day schedule, plus row-count checks so an empty load counts as a failure, and a flat-line check for series that normally move. To limit damage, models and tools check input freshness and caveat or refuse, answers show the as-of date, and there's a runbook for contacting the vendor and backfilling. When it resumes, I backfill idempotently, re-run affected outputs and tell users which results were affected.


## Backfills and operations

### 9. What is a backfill, and how do you do one safely?

<details><summary>Understand it</summary>

```text
WHAT
Re-running a pipeline for a past range: to fill a gap, apply a bug fix to history, add a new column/feature for old dates, or load a new source's history.

SAFELY
1. Idempotent jobs, so re-running doesn't duplicate.
2. Process in batches (a month at a time), with throttling; big backfills compete with production for the database.
3. Run off-peak; watch database CPU, locks and connections.
4. Write to a staging table and swap, or overwrite partition by partition in transactions.
5. Validate after each batch (row counts, checks), and compare with what was there.
6. Keep point-in-time semantics: a backfill of history must not pretend you knew things earlier than you did (publication dates stay true; ingested_at = now).
7. Have a rollback: a backup/PITR point before starting.
8. Communicate: downstream consumers may see changed history.

REAL LESSON
A large rebuild on a shared dev database took it down for two days. Batch, throttle, and run heavy rebuilds somewhere isolated first.
```

</details>

**Answer:** A backfill re-runs the pipeline for a past range, to fill a gap, fix history after a bug, or add a feature for old dates. To do it safely the job must be idempotent; I run it in batches with throttling, off-peak, while watching database load; write to staging and swap, or overwrite partitions in transactions; validate each batch; keep true publication dates so history doesn't pretend we knew things earlier; take a backup or PITR point first; and tell downstream users that history changed. I've seen a large rebuild take a shared dev database down, so heavy runs go somewhere isolated first.

### 10. How do you schedule and orchestrate pipelines? Cron vs Airflow?

<details><summary>Understand it</summary>

```text
CRON / CLOUD SCHEDULER
Run a command at a time. Simple, reliable for a few independent jobs. Missing: dependencies between jobs, retries with backoff, backfill UI, visibility of history.

ORCHESTRATORS (Airflow, Dagster, Prefect, Cloud Composer, Step Functions)
- Jobs as a DAG: B runs after A succeeds.
- Retries, timeouts, alerts on failure, SLAs.
- Backfills over date ranges built in (each run has a logical date).
- History and logs per run; lineage (Dagster) and data-aware scheduling.
Cost: another system to run and learn.

DECISION
A handful of jobs: cron + good logging + alerts + idempotent scripts. Many interdependent jobs, backfills, a team: an orchestrator.

DESIGN TIPS
- Each task idempotent and parameterised by date.
- Schedule after the source's publication time (+ buffer), not at midnight by habit.
- Mind time zones and business-day calendars.
- Alert on failure AND on 'didn't run'.
```

</details>

**Answer:** For a few independent jobs, cron or Cloud Scheduler with idempotent scripts, logging and alerts is enough. When jobs depend on each other and we need retries, timeouts, backfills over date ranges and run history, I'd use an orchestrator like Airflow, Dagster or Prefect, at the cost of running another system. Either way each task is idempotent and parameterised by date, scheduled after the source actually publishes, time-zone and business-day aware, and alerts both on failure and on not running at all.

### 11. How do you version data and make results reproducible?

<details><summary>Understand it</summary>

```text
WHY
'The model gave X last month; why does it give Y now?' You need to know which data, code and model produced each output.

HOW
1. Immutable raw data with load timestamps; derived data reproducible from raw + code version.
2. Bitemporal storage so any as-of view can be rebuilt.
3. Snapshot or tag datasets used for training/evaluation (DVC, lakeFS, Delta/Iceberg time travel, or a dated table copy).
4. Log with every prediction/answer: model version, code commit, data as-of date, feature snapshot id.
5. Pin dependencies; build in containers.

FOR RAG
Document versions with content hashes; the index records which version of each document was embedded; answers cite document id + version.
```

</details>

**Answer:** I keep raw data immutable with load timestamps so derived data can be rebuilt from raw plus a code version, store data bitemporally so any as-of view can be reconstructed, snapshot the datasets used for training and evaluation with something like Delta time travel, DVC or a dated copy, and log with every prediction the model version, code commit and data as-of date. For RAG, documents carry versions and hashes, and answers cite the document version.


## SQL

### 12. Write a query to get each month's latest value as known on a given date.

<details><summary>Understand it</summary>

```text
THE PATTERN: ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ... DESC) = 1

SELECT value_date, value, published_at FROM (
  SELECT *, ROW_NUMBER() OVER (
           PARTITION BY value_date
           ORDER BY published_at DESC) AS rn
  FROM observations
  WHERE series = 'indicator'
    AND published_at <= '2023-01-01'      -- only what was known then
) t
WHERE rn = 1;

HOW TO EXPLAIN IT
1. Filter to releases published on or before the date: no future data.
2. Within each period, number releases newest first.
3. Keep number 1: the latest known release per period.

ALTERNATIVES
- Correlated subquery: WHERE published_at = (SELECT MAX(published_at) ... <= date).
- Postgres: SELECT DISTINCT ON (value_date) ... ORDER BY value_date, published_at DESC.
- Joining two tables as-of (each trade with the latest quote before it): LATERAL join in Postgres, ASOF JOIN in DuckDB/ClickHouse/Snowflake, merge_asof in pandas.
```

</details>

**Answer:** I filter to releases published on or before the date so nothing from the future gets in, then use ROW_NUMBER partitioned by period and ordered by publication date descending, and keep row number one: the latest known release for each period. In Postgres DISTINCT ON does the same. For joining two tables as-of, like each trade to the latest quote before it, I'd use a LATERAL join, an ASOF JOIN in DuckDB or Snowflake, or merge_asof in pandas.

### 13. How do you find duplicates and gaps in time-series data with SQL?

<details><summary>Understand it</summary>

```text
DUPLICATES
SELECT series, value_date, published_at, COUNT(*)
FROM observations GROUP BY 1,2,3 HAVING COUNT(*) > 1;
Remove keeping one: ROW_NUMBER() OVER (PARTITION BY key ORDER BY ingested_at DESC) and delete rn > 1.

GAPS WITH LAG()
SELECT d, prev FROM (
  SELECT d, LAG(d) OVER (ORDER BY d) AS prev FROM (SELECT DISTINCT value_date AS d FROM observations)
) WHERE (months between prev and d) > 1;
For daily business data, compare against a calendar table of expected business days (LEFT JOIN calendar, WHERE data IS NULL). That handles weekends and holidays correctly.

OTHER WINDOW FUNCTIONS INTERVIEWERS LIKE
- Change vs previous: value - LAG(value) OVER (PARTITION BY id ORDER BY d)
- Running average: AVG(value) OVER (ORDER BY d ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
- Rank within group: RANK() / DENSE_RANK() OVER (PARTITION BY category ORDER BY score DESC)
```

</details>

**Answer:** Duplicates: GROUP BY the natural key HAVING COUNT greater than one, and to remove them, ROW_NUMBER over the key ordered by load time, deleting everything after row one. Gaps: LAG over the date to compare each date with the previous one and flag jumps bigger than one period. For daily business data I left-join a calendar table of expected business days, so weekends and holidays aren't false gaps. LAG also gives changes versus the previous value, and AVG over a window frame gives running averages.


## Scenarios

### 14. Your model looked great in backtesting but is poor in production. What do you check?

<details><summary>Understand it</summary>

```text
CHECK IN THIS ORDER
1. Look-ahead in the data: were features joined on value date with today's revised data? Were features available at prediction time (publication lag)? Rebuild with as-of queries.
2. Target leakage: does any feature encode the answer (computed after the target period, or from the target itself)?
3. Survivorship: did the history only include entities that exist today?
4. Overfitting / selection: many variants tried, the best picked on the same data? Use proper out-of-sample (CPCV with purging and embargo, a true holdout), and adjust for multiple testing (deflated Sharpe, PBO).
5. Train/serve skew: production computes features differently from training (different code path, units, time zone, missing-value handling).
6. Regime change: the world changed (drift).
7. Costs and frictions ignored in the backtest.

THE ATTITUDE
'If a result looks too good, assume a bug until proven otherwise.'
```

</details>

**Answer:** First look-ahead: were features joined on today's revised data or used before they were published? Then target leakage, survivorship bias, and selection bias from trying many variants on the same data, which I'd test with proper out-of-sample methods like purged cross-validation, a true holdout and multiple-testing adjustments. Then train-serve skew, where production computes features differently, then regime change and ignored costs. My default is that a result that looks too good is a bug until proven otherwise.

### 15. Design the data layer for an AI assistant that answers questions about market data.

<details><summary>Understand it</summary>

```text
LAYERS
1. Ingestion: scheduled jobs per source (vendor API, SFTP files), raw landed immutably with received time; parsed into typed tables.
2. Storage: Postgres with bitemporal tables (value_date, published_at, ingested_at), partitioned by date; reference data (instruments, calendars) with effective dates.
3. Quality: freshness, gaps against a business-day calendar, ranges, duplicates, unit-shift checks after every load; quarantine bad batches; alerts.
4. Features and model scores: computed by idempotent batch jobs using as-of queries; stored with model version and as-of date.
5. Serving to the assistant: tools (MCP) that take as_of, read only through as-of views, return the as-of date used and data caveats (excluded items, staleness).
6. Documents (research notes, prospectuses): object storage + versioned chunks and embeddings with publication dates for RAG.
7. Operations: orchestration, backfill procedure, backups + PITR, lineage from answer -> tool -> data version.
```

</details>

**Answer:** Scheduled ingestion per source lands raw data immutably, then parses it into typed bitemporal tables in Postgres, with reference data and a business-day calendar. Quality checks run after every load with quarantine and alerts. Features and model scores are computed by idempotent batch jobs using as-of queries and stored with the model version. The assistant reaches data only through tools that take an as-of date, read as-of views, and return the date used plus caveats like excluded items or staleness. Documents for RAG are versioned with publication dates. Around it: orchestration, a backfill procedure, backups and lineage from answer to data version.


## Glossary

| Term | Meaning |
|---|---|
| Idempotent | Running it again changes nothing; safe to retry and backfill. |
| Natural key | Columns that identify a fact (series, value_date, published_at); enforced unique. |
| Upsert | Insert, or update/ignore if the key exists (ON CONFLICT, MERGE). |
| Publication lag | Time between the period a value describes and when it becomes public. |
| Revision / vintage | A later corrected release of the same value / which release a value is. |
| Bitemporal | Storing both the period a fact describes and when it became known. |
| As-of query | Returns what was known on a given date. |
| Look-ahead bias | Using information that was not yet available at that time. |
| Survivorship bias | History that only includes entities that still exist. |
| Train/serve skew | Features computed differently in production than in training. |
| Freshness | How recent the latest data is vs the expected schedule. |
| Backfill | Re-running a pipeline for a past range. |
| Quarantine | Holding a failed batch aside instead of loading it. |
| Orchestrator | Airflow/Dagster/Prefect: DAGs, retries, backfills, run history. |
| Window function | SQL over a set of related rows: ROW_NUMBER, LAG, running AVG. |
| ASOF JOIN / merge_asof | Join each row to the latest row of another table at or before its time. |
| Lineage | Tracing an output back to the exact data and code that produced it. |
