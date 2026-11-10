"""A small, honest data pipeline: idempotent ingestion, point-in-time storage, as-of queries, quality checks.

The data: a monthly economic indicator (synthetic). Like real ones, it is
  - PUBLISHED LATE: the value for March appears on about 12 April (publication lag)
  - REVISED: a first estimate, then a revised number a month later
So for every value we store TWO times (bitemporal):
  value_date    - the period the number describes (2024-03)
  published_at  - when the world could first know this number (2024-04-12)
and ingested_at  - when OUR pipeline loaded it (for debugging and backfills).

An as-of query answers: "what did we know on date D?" Using anything else in a backtest or an
AI answer is look-ahead: the model 'sees' numbers that did not exist yet.

Run:  python day14_pipelines/pipeline.py
"""
from __future__ import annotations

import datetime as dt
import random
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    series       TEXT NOT NULL,
    value_date   TEXT NOT NULL,     -- period the value describes, YYYY-MM
    published_at TEXT NOT NULL,     -- when it became public, YYYY-MM-DD
    value        REAL NOT NULL,
    vintage      TEXT NOT NULL,     -- 'first' or 'revised'
    ingested_at  TEXT NOT NULL,
    PRIMARY KEY (series, value_date, published_at)   -- natural key: re-running cannot duplicate
);
CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, started TEXT, rows_seen INT, rows_new INT);
"""


def connect(path: str | Path = ":memory:") -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.executescript(SCHEMA)
    return con


def month_add(ym: str, k: int) -> str:
    y, m = map(int, ym.split("-"))
    m += k
    y, m = y + (m - 1) // 12, (m - 1) % 12 + 1
    return f"{y:04d}-{m:02d}"


def source_feed(start: str = "2022-01", months: int = 36, seed: int = 14) -> list[dict]:
    """What a vendor API would return: every release (first and revised) of the indicator."""
    rng = random.Random(seed)
    rows, x = [], 0.0
    for i in range(months):
        ym = month_add(start, i)
        x = 0.6 * x + rng.gauss(0, 1)                       # the true value (persistent, like real macro data)
        first = round(x + rng.gauss(0, 0.6), 3)            # first estimate is noisy
        nxt = month_add(ym, 1)
        rows.append({"series": "indicator", "value_date": ym, "published_at": f"{nxt}-12", "value": first, "vintage": "first"})
        rev = month_add(ym, 2)
        rows.append({"series": "indicator", "value_date": ym, "published_at": f"{rev}-12", "value": round(x, 3), "vintage": "revised"})
    return rows


def ingest(con: sqlite3.Connection, rows: list[dict], run_id: str) -> dict:
    """Idempotent: running the same batch twice changes nothing. Safe to retry and to backfill."""
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    before = con.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    with con:                                             # one transaction: all rows or none
        con.executemany(
            "INSERT INTO observations (series, value_date, published_at, value, vintage, ingested_at) "
            "VALUES (:series, :value_date, :published_at, :value, :vintage, :now) "
            "ON CONFLICT (series, value_date, published_at) DO NOTHING",
            [{**r, "now": now} for r in rows])
        after = con.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        con.execute("INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?)", (run_id, now, len(rows), after - before))
    return {"run_id": run_id, "rows_seen": len(rows), "rows_new": after - before}


def as_of(con: sqlite3.Connection, series: str, value_date: str, known_at: str) -> float | None:
    """The value for value_date as it was known on known_at (latest release published on or before that day)."""
    row = con.execute(
        "SELECT value FROM observations WHERE series=? AND value_date=? AND published_at<=? "
        "ORDER BY published_at DESC LIMIT 1", (series, value_date, known_at)).fetchone()
    return row[0] if row else None


def latest_known(con: sqlite3.Connection, series: str, known_at: str) -> tuple[str, float] | None:
    """The most recent period whose value was public on known_at. This is what a model may use that day."""
    row = con.execute(
        "SELECT value_date, value FROM observations o WHERE series=? AND published_at<=? "
        "ORDER BY value_date DESC, published_at DESC LIMIT 1", (series, known_at)).fetchone()
    return (row[0], row[1]) if row else None


def quality_checks(con: sqlite3.Connection, series: str, today: str, max_age_days: int = 45) -> list[str]:
    """Problems found; empty list = healthy. Run after every load, alert on any problem."""
    problems = []
    last_pub = con.execute("SELECT MAX(published_at) FROM observations WHERE series=?", (series,)).fetchone()[0]
    if last_pub is None:
        return [f"{series}: no data at all"]
    age = (dt.date.fromisoformat(today) - dt.date.fromisoformat(last_pub)).days
    if age > max_age_days:
        problems.append(f"STALE: last release {last_pub}, {age} days old (limit {max_age_days})")
    months = [r[0] for r in con.execute(
        "SELECT DISTINCT value_date FROM observations WHERE series=? ORDER BY value_date", (series,))]
    for a, b in zip(months, months[1:]):
        if month_add(a, 1) != b:
            problems.append(f"GAP: nothing between {a} and {b}")
    bad = con.execute("SELECT COUNT(*) FROM observations WHERE series=? AND (value IS NULL OR ABS(value) > 10)",
                      (series,)).fetchone()[0]
    if bad:
        problems.append(f"RANGE: {bad} values outside the plausible range")
    late = con.execute("SELECT COUNT(*) FROM observations WHERE series=? AND published_at < value_date || '-28'",
                       (series,)).fetchone()[0]
    if late:
        problems.append(f"TIME TRAVEL: {late} values published before their period ended")
    return problems


if __name__ == "__main__":
    con = connect()
    feed = source_feed()
    print("first load :", ingest(con, feed, "run-1"))
    print("re-run     :", ingest(con, feed, "run-2"), "<- idempotent, nothing duplicated")

    print("\nWhat was known about 2024-03, on different days:")
    for day in ["2024-03-31", "2024-04-11", "2024-04-12", "2024-05-12"]:
        print(f"  on {day}: {as_of(con, 'indicator', '2024-03', day)}")
    print("\nOn 2024-04-01 a model may use:", latest_known(con, "indicator", "2024-04-01"),
          " (February's first estimate, not March)")

    print("\nQuality on 2024-12-20:", quality_checks(con, "indicator", "2024-12-20") or "healthy")
    con.execute("DELETE FROM observations WHERE value_date='2023-06'")
    print("After a month goes missing:", quality_checks(con, "indicator", "2024-12-20"))
    print("Months later, no new loads:", quality_checks(con, "indicator", "2025-06-01"))

    print("\nBackfill the missing month (only those rows):",
          ingest(con, [r for r in feed if r["value_date"] == "2023-06"], "backfill-2023-06"))
    assert quality_checks(con, "indicator", "2024-12-20") == []
    assert as_of(con, "indicator", "2024-03", "2024-04-11") is None
    print("ok: idempotent, point-in-time, checks catch gap and staleness, backfill repairs")
