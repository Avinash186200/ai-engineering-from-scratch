"""Train the fund ranker honestly: shuffled CV (leaky) vs walk-forward vs purged + embargoed CV.

The target looks 21 business days ahead, so neighbouring rows share future information.
Shuffled K-fold leaks it; purging and an embargo remove it. Metrics are illustrative
(synthetic data). Run:  python day07_ml/train_ranker.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.fund_model import TARGET, features, load_panel  # noqa: E402

HORIZON, EMBARGO = 21, 5


def model():
    return GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=0)


def daily_rank_ic(df, pred):
    d = df.assign(pred=pred)
    ics = d.groupby("date").apply(lambda g: g["pred"].corr(g[TARGET], method="spearman"),
                                  include_groups=False)
    return float(ics.mean())


def top5_spread(df, pred):
    d = df.assign(pred=pred)
    top = d.groupby("date", group_keys=False).apply(lambda g: g.nlargest(5, "pred"), include_groups=False)
    return float(top[TARGET].mean() - d[TARGET].mean())


def fit_score(train, test):
    m = model().fit(features(train), train[TARGET])
    p = m.predict(features(test).reindex(columns=features(train).columns, fill_value=0))
    return daily_rank_ic(test, p), top5_spread(test, p)


def report(name, scores):
    ic, sp = np.mean([s[0] for s in scores]), np.mean([s[1] for s in scores])
    print(f"{name:<26} folds={len(scores)}  rank IC={ic:+.3f}  top-5 excess 21d return={sp:+.2%}")


def shuffled_cv(df, k=5):
    out = []
    for tr, te in KFold(k, shuffle=True, random_state=0).split(df):
        out.append(fit_score(df.iloc[tr], df.iloc[te]))
    return out


def walk_forward(df, dates, n_folds=4):
    out, step = [], len(dates) // (n_folds + 1)
    for f in range(1, n_folds + 1):
        cut = dates[f * step]
        test_end = dates[min((f + 1) * step, len(dates) - 1)]
        train_end = dates[max(f * step - HORIZON, 0)]           # purge: labels must end before test
        train = df[df["date"] < train_end]
        test = df[(df["date"] >= cut) & (df["date"] < test_end)]
        out.append(fit_score(train, test))
    return out


def purged_kfold(df, dates, k=5):
    out = []
    for block in np.array_split(np.arange(len(dates)), k):
        lo, hi = block[0], block[-1]
        test_dates = set(dates[lo:hi + 1])
        banned = set(dates[max(lo - HORIZON, 0):min(hi + 1 + EMBARGO, len(dates))])
        train = df[~df["date"].isin(banned)]
        test = df[df["date"].isin(test_dates)]
        out.append(fit_score(train, test))
    return out


if __name__ == "__main__":
    df = load_panel().dropna(subset=[TARGET]).reset_index(drop=True)
    dates = sorted(df["date"].unique())
    print(f"panel: {len(df)} rows, {df['fund'].nunique()} funds, {len(dates)} days "
          f"(horizon {HORIZON}d, embargo {EMBARGO}d)\n")
    report("shuffled K-fold (leaky)", shuffled_cv(df))
    report("walk-forward", walk_forward(df, dates))
    report("purged + embargoed K-fold", purged_kfold(df, dates))
    print("\nIf the leaky score is much higher, the gap is leakage, not skill.")
