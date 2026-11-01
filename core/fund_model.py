"""The ranking "tool": train a small model on the synthetic fund panel and rank funds.

    from core.fund_model import rank_funds
    rank_funds("2024-06-03", top_n=3)

Errors are returned as {"error": "..."} instead of raised, so agents can read them.
"""
from __future__ import annotations

import datetime as dt
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "funds.csv"
NUMERIC = ["momentum_3m", "volatility_3m", "expense_ratio", "aum_cr", "fund_age_yrs"]
TARGET = "fwd_return_21d"


def load_panel() -> pd.DataFrame:
    if not DATA.exists():  # build the data on first use
        sys.path.insert(0, str(ROOT))
        from data.make_data import make_panel
        make_panel().to_csv(DATA, index=False)
    return pd.read_csv(DATA)


def features(df: pd.DataFrame) -> pd.DataFrame:
    X = df[NUMERIC].copy()
    return X.join(pd.get_dummies(df["category"], prefix="cat", dtype=float))


@lru_cache(maxsize=1)
def _model_and_panel():
    df = load_panel()
    train = df.dropna(subset=[TARGET])
    train = train[train["date"] < "2024-07-01"]          # train on the past only
    X = features(train)
    model = GradientBoostingRegressor(n_estimators=150, max_depth=3, random_state=0)
    model.fit(X, train[TARGET])
    return model, list(X.columns), df


def rank_funds(as_of: str | None = None, top_n: int = 5) -> dict:
    model, cols, df = _model_and_panel()
    if as_of is None:
        as_of = df["date"].max()
    try:
        day = dt.date.fromisoformat(str(as_of))
    except ValueError:
        return {"error": f"bad date '{as_of}': use YYYY-MM-DD"}
    if day.weekday() >= 5:
        return {"error": f"{as_of} is a weekend: markets are closed"}
    if not isinstance(top_n, int) or not 1 <= top_n <= 30:
        return {"error": "top_n must be an integer between 1 and 30"}
    snap = df[df["date"] == day.isoformat()]
    if snap.empty:
        return {"error": f"no data for {as_of} (range {df['date'].min()} .. {df['date'].max()})"}
    X = features(snap).reindex(columns=cols, fill_value=0.0)
    snap = snap.assign(pred=model.predict(X)).sort_values("pred", ascending=False)
    top = [{"rank": i + 1, "fund": r.fund, "predicted_return": round(float(r.pred), 4)}
           for i, r in enumerate(snap.head(top_n).itertuples())]
    return {"as_of": day.isoformat(), "top": top}


def fund_info(name: str) -> dict:
    df = load_panel()
    hit = df[df["fund"].str.lower() == str(name).lower()]
    if hit.empty:
        return {"error": f"unknown fund '{name}'"}
    last = hit.iloc[-1]
    return {"fund": last["fund"], "category": last["category"], "nav": float(last["nav"]),
            "expense_ratio": float(last["expense_ratio"]), "aum_cr": float(last["aum_cr"]),
            "as_of": last["date"]}


GLOSSARY = {
    "nav": "Net Asset Value: the per-unit price of a fund, computed once a day.",
    "expense ratio": "The yearly fee a fund charges, as a percent of your money.",
    "sip": "Systematic Investment Plan: investing a fixed amount every month.",
    "exit load": "A fee charged if you redeem units before a minimum holding period.",
    "aum": "Assets Under Management: the total money a fund manages, in crore rupees.",
    "momentum": "How much a fund's NAV has risen over a recent window, e.g. 3 months.",
}


def lookup_term(term: str) -> dict:
    key = str(term).lower().strip()
    if key in GLOSSARY:
        return {"term": key, "definition": GLOSSARY[key]}
    return {"error": f"term '{term}' not in glossary; known: {sorted(GLOSSARY)}"}


if __name__ == "__main__":
    print(rank_funds("2024-11-04", top_n=3))
    print(rank_funds("2024-11-09"))
    print(rank_funds("not-a-date"))
