# Day 14: Data pipelines and point-in-time data

Models and AI assistants are only as good as the data they are fed. This day builds a small pipeline the way production
teams do: idempotent loads, every release stored with its publication date, as-of queries, quality checks and backfills,
and shows how look-ahead leakage makes a model look far better than it is.

| Video | Short |
|---|---|
| [Day 14, full episode](https://youtu.be/RcC7qz3XHdY) | [Same model, same data. 6x better on paper.](https://youtube.com/shorts/GMXoIRaFR-k) |

| File | What it is |
|---|---|
| [pipeline.py](pipeline.py) | Bitemporal table (value date + publication date), idempotent ingestion, as-of queries, freshness/gap/range/time-travel checks, backfill |
| [leakage.py](leakage.py) | The same model evaluated with a naive join vs a point-in-time join: R^2 about 0.69 vs 0.12 |
| [sql_examples.py](sql_examples.py) | Interview SQL on the same table: as-of with ROW_NUMBER, dedupe, gaps with LAG, revisions, running averages, upsert |
| [LAB.md](LAB.md) | Seven steps, from loading twice to adding your own daily series |
| [INTERVIEW_QA.md](INTERVIEW_QA.md) | Interview questions with full explanations and spoken answers |

## Quick start
```bash
python day14_pipelines/pipeline.py
python day14_pipelines/leakage.py
python day14_pipelines/sql_examples.py
```

## Five lessons from a real production AI platform
1. Missing upstream data broke models before any AI problem did. Monitor freshness and gaps on every feed.
2. Store when a value was published, not just what period it describes. Without it you cannot answer "what did we know then?"
3. Make every load idempotent. Retries and backfills then become safe, routine operations.
4. Backfills are real load. One large rebuild took a shared development database down; batch and throttle them.
5. If a result looks too good, check the joins for look-ahead first.
