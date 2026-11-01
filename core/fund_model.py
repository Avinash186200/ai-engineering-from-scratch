"""The ranking "tool": train small models on the synthetic fund panel and rank funds.

    from core.fund_model import rank_funds
    rank_funds("2025-06-19", top_n=3)

Result shape:
    {"as_of": "2025-06-19", "model": "quantile", "n_scored": 120,
     "top": [{"rank": 1, "fund": "...", "predicted_return": 0.0053, "nav": 48.72}, ...],
     "excluded": [{"fund": "...", "reason": "..."}],
     "caveat": "Research signal from a backtested model, not advice."}

Data problems (weekend, bad date, outside the data) come back as {"error": "..."} instead of
being raised, so an agent can read them. A wrong model name raises ValueError: the agent's
tools node turns that into an error result too.
"""
from __future__ import annotations

import datetime as dt
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "funds.csv"
NUMERIC = ["momentum_3m", "volatility_3m", "expense_ratio"]
CATEGORIES = ["equity", "debt", "hybrid"]
H = 20                                   # label horizon in trading days
TARGET = f"fwd_return_{H}d"
TRAIN_END = "2025-01-01"                 # models learn from the past only
MODELS = ["ridge", "quantile"]
DEFAULT_MODEL = "quantile"
MAX_TOP_N = 50
CAVEAT = "Research signal from a backtested model, not advice."


def load_panel() -> pd.DataFrame:
    if not DATA.exists():  # build the data on first use
        sys.path.insert(0, str(ROOT))
        from data.make_data import make_panel
        make_panel().to_csv(DATA, index=False)
    return pd.read_csv(DATA)


def features(df: pd.DataFrame) -> pd.DataFrame:
    X = df[NUMERIC].astype(float).copy()
    for c in CATEGORIES:
        X[f"cat_{c}"] = (df["category"] == c).astype(float)
    return X


def _new_model(name: str):
    if name == "ridge":
        return make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    if name == "quantile":               # median regression: robust to outlier months
        return HistGradientBoostingRegressor(loss="quantile", quantile=0.5, max_iter=150,
                                             max_depth=3, learning_rate=0.05,
                                             random_state=0)
    raise ValueError(f"unknown model '{name}'; choose one of {MODELS}")


@lru_cache(maxsize=1)
def _panel() -> pd.DataFrame:
    return load_panel()


@lru_cache(maxsize=None)
def _trained(name: str):
    df = _panel()
    train = df.dropna(subset=NUMERIC + [TARGET])
    dates = sorted(train["date"].unique())
    cut = [d for d in dates if d < TRAIN_END]
    purge_from = cut[-H] if len(cut) > H else TRAIN_END   # drop labels that peek past TRAIN_END
    train = train[train["date"] < purge_from]
    return _new_model(name).fit(features(train), train[TARGET])


def _is_business_day(day: dt.date) -> bool:
    return day.weekday() < 5


def rank_funds(as_of: str | None = "", top_n: int = 5, model: str = DEFAULT_MODEL,
               category: str | None = None) -> dict:
    """Rank funds by predicted 20-trading-day return on one business day (YYYY-MM-DD)."""
    if model not in MODELS:
        raise ValueError(f"unknown model '{model}'; choose one of {MODELS}")
    df = _panel()
    if not as_of:
        as_of = df["date"].max()
    try:
        day = dt.date.fromisoformat(str(as_of))
    except ValueError:
        return {"error": f"Bad date '{as_of}': use YYYY-MM-DD, for example 2025-06-19."}
    if not isinstance(top_n, int) or isinstance(top_n, bool) or not 1 <= top_n <= MAX_TOP_N:
        return {"error": f"top_n must be an integer between 1 and {MAX_TOP_N}."}
    if category is not None and category not in CATEGORIES:
        return {"error": f"Unknown category '{category}'; choose one of {CATEGORIES}."}
    first, last = df["date"].min(), df["date"].max()
    if not first <= day.isoformat() <= last:
        return {"error": f"No data for {day.isoformat()}: outside the data range "
                         f"{first} to {last}."}
    if not _is_business_day(day):
        return {"error": f"No data for {day.isoformat()} (not a business day?). "
                         "Try a nearby weekday."}
    snap = df[df["date"] == day.isoformat()]
    if category:
        snap = snap[snap["category"] == category]
    if snap.empty:
        return {"error": f"No data for {day.isoformat()}. Try a nearby weekday."}
    young = snap[NUMERIC].isna().any(axis=1)
    excluded = [{"fund": f, "reason": "less than 3 months of history"}
                for f in snap.loc[young, "fund"]]
    snap = snap[~young]
    pred = _trained(model).predict(features(snap))
    snap = snap.assign(pred=pred).sort_values("pred", ascending=False)
    top = [{"rank": i + 1, "fund": r.fund, "predicted_return": round(float(r.pred), 4),
            "nav": round(float(r.nav), 2)}
           for i, r in enumerate(snap.head(top_n).itertuples())]
    return {"as_of": day.isoformat(), "model": model, "n_scored": int(len(snap)), "top": top,
            "excluded": excluded, "caveat": CAVEAT}


def compare_models(as_of: str | None = "", top_n: int = 3) -> dict:
    """Top funds from both ranking models, side by side (the Day 3 exercise, solved)."""
    out = {m: rank_funds(as_of, top_n, model=m) for m in MODELS}
    errs = [r["error"] for r in out.values() if "error" in r]
    if errs:
        return {"error": errs[0]}
    tops = {m: [row["fund"] for row in r["top"]] for m, r in out.items()}
    return {"as_of": out[DEFAULT_MODEL]["as_of"], **tops,
            "agree_on_top": len({t[0] for t in tops.values()}) == 1, "caveat": CAVEAT}


def fund_info(name: str) -> dict:
    df = _panel()
    hit = df[df["fund"].str.lower() == str(name).lower().strip()]
    if hit.empty:
        return {"error": f"Unknown fund '{name}'. Check the exact fund name."}
    last = hit.iloc[-1]
    return {"fund": last["fund"], "category": last["category"], "nav": round(float(last["nav"]), 2),
            "expense_ratio": float(last["expense_ratio"]), "aum_cr": float(last["aum_cr"]),
            "as_of": last["date"]}


def model_info() -> dict:
    """Facts about the ranking models themselves: features, target, training window."""
    cols = list(features(_panel().head(1)).columns)
    return {"models": MODELS, "default_model": DEFAULT_MODEL, "n_features": len(cols),
            "features": cols, "target": f"next {H} trading days' return",
            "trained_before": TRAIN_END, "data_range": [_panel()["date"].min(), _panel()["date"].max()]}


GLOSSARY = {
    "nav": ("NAV", "Net asset value: the price of one unit of a fund, computed once a day."),
    "expense ratio": ("Expense ratio", "The yearly fee a fund charges, as a percentage of your money."),
    "sip": ("SIP", "Systematic investment plan: investing a fixed amount every month."),
    "exit load": ("Exit load", "A fee charged if you redeem units before a minimum holding period."),
    "aum": ("AUM", "Assets under management: the total money a fund manages, in crore rupees."),
    "momentum": ("Momentum", "How much a fund's NAV has risen over a recent window, e.g. 3 months."),
    "elss": ("ELSS", "A tax-saving equity fund with a three-year lock-in."),
}


def lookup_definition(term: str) -> dict:
    key = str(term).lower().strip().rstrip("?.")
    for prefix in ("an ", "a ", "the "):
        key = key.removeprefix(prefix)
    if key in GLOSSARY:
        name, definition = GLOSSARY[key]
        return {"term": name, "definition": definition}
    return {"error": f"Unknown term '{term}'. Known terms: {sorted(GLOSSARY)}."}


lookup_term = lookup_definition          # older name, kept as an alias


if __name__ == "__main__":
    print(rank_funds("2025-06-19", top_n=3))
    print(rank_funds("2025-06-21"))
    print(rank_funds("not-a-date"))
    print(model_info())
