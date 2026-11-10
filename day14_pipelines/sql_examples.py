"""The SQL patterns data and AI interviews ask about, run on the Day 14 table (SQLite, no setup).

  1. As-of join with a window function (latest release known on a date)
  2. Deduplicate: keep one row per key with ROW_NUMBER()
  3. Find gaps with LAG()
  4. Change between releases (revision size) with LAG() over vintages
  5. Running average with a window frame
  6. Upsert (insert or update) for idempotent loads

Run:  python day14_pipelines/sql_examples.py
"""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from day14_pipelines.pipeline import connect, ingest, source_feed

QUERIES = {
    "1. As-of: each month's value as known on 2023-01-01": """
        SELECT value_date, value, published_at FROM (
          SELECT *, ROW_NUMBER() OVER (PARTITION BY value_date ORDER BY published_at DESC) AS rn
          FROM observations WHERE series = 'indicator' AND published_at <= '2023-01-01')
        WHERE rn = 1 ORDER BY value_date DESC LIMIT 3""",
    "2. Deduplicate: one row per (series, value_date), the latest release": """
        SELECT COUNT(*) AS rows_before,
               (SELECT COUNT(*) FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY series, value_date
                                       ORDER BY published_at DESC) rn FROM observations) WHERE rn = 1) AS rows_after
        FROM observations""",
    "3. Gaps: months whose previous month is missing": """
        SELECT value_date, prev FROM (
          SELECT value_date, LAG(value_date) OVER (ORDER BY value_date) AS prev
          FROM (SELECT DISTINCT value_date FROM observations))
        WHERE prev IS NOT NULL
          AND CAST(substr(value_date,1,4) AS INT)*12 + CAST(substr(value_date,6,2) AS INT)
            - CAST(substr(prev,1,4) AS INT)*12 - CAST(substr(prev,6,2) AS INT) > 1""",
    "4. Revisions: how much did the second release change the first?": """
        SELECT value_date, ROUND(value - LAG(value) OVER (PARTITION BY value_date ORDER BY published_at), 3) AS revision
        FROM observations WHERE series = 'indicator'
        ORDER BY ABS(revision) DESC NULLS LAST LIMIT 3""",
    "5. Running 3-month average of revised values": """
        SELECT value_date, ROUND(AVG(value) OVER (ORDER BY value_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 3) AS avg3
        FROM observations WHERE vintage = 'revised' ORDER BY value_date DESC LIMIT 3""",
}

UPSERT = """INSERT INTO observations (series, value_date, published_at, value, vintage, ingested_at)
VALUES ('indicator', '2022-01', '2022-03-12', 9.99, 'revised', 'now')
ON CONFLICT (series, value_date, published_at) DO UPDATE SET value = excluded.value, ingested_at = excluded.ingested_at"""

if __name__ == "__main__":
    con = connect()
    feed = source_feed()
    ingest(con, [r for r in feed if r["value_date"] != "2023-06"], "load")    # leave a gap to find
    for title, q in QUERIES.items():
        rows = con.execute(q).fetchall()
        print(f"\n{title}\n  {rows}")
    con.execute(UPSERT)
    print("\n6. Upsert: the corrected value replaced the old one, no duplicate row:",
          con.execute("SELECT COUNT(*), MAX(value) FROM observations WHERE value_date='2022-01' AND published_at='2022-03-12'").fetchone())
    assert con.execute(QUERIES["3. Gaps: months whose previous month is missing"]).fetchall() == [("2023-07", "2023-05")]
    print("\nok: all six patterns ran")
