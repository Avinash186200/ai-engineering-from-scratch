"""Train the fund ranker honestly: leaky shuffled K-fold vs walk-forward vs purged + embargoed CV,
then combinatorial purged CV (CPCV): 6 blocks, 2 test blocks, 15 splits, 5 backtest paths.

The target looks H = 20 trading days ahead, so neighbouring rows share future information.
Shuffled K-fold leaks it; purging and an embargo remove it. Metrics are illustrative
(synthetic data). Run:  python day07_ml/train_ranker.py   (about a minute)
"""
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import KFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.fund_model import NUMERIC, TARGET, features, load_panel  # noqa: E402

H = 20        # label horizon: next 20 trading days
EMBARGO = 20  # gap after each test block


def purged_train_days(all_days, test_start, test_end):
    keep = []
    for d in all_days:
        label_end = d + H                      # this row's answer window
        overlaps = d <= test_end and label_end >= test_start
        in_embargo = test_end < d <= test_end + EMBARGO
        if not overlaps and not in_embargo:
            keep.append(d)
    return keep


def model():
    return HistGradientBoostingRegressor(max_iter=100, max_depth=3, learning_rate=0.05,
                                         random_state=0)


def daily_rank_ic(df, pred):
    """Mean over days of the Spearman correlation between predicted and actual return."""
    d = df.assign(pred=pred)
    r = d.groupby("date")[["pred", TARGET]].rank()
    return float(r.groupby(d["date"]).corr().xs("pred", level=1)[TARGET].mean())


def fit_score(train, test):
    m = model().fit(features(train), train[TARGET])
    return daily_rank_ic(test, m.predict(features(test)))


def report(name, scores):
    print(f"{name:<28} folds={len(scores):<3} rank IC={np.mean(scores):+.3f}  "
          f"(min {np.min(scores):+.3f}, max {np.max(scores):+.3f})")


def shuffled_cv(df, k=5):
    return [fit_score(df.iloc[tr], df.iloc[te])
            for tr, te in KFold(k, shuffle=True, random_state=0).split(df)]


def walk_forward(df, n_folds=4):
    n_days = df["day"].max() + 1
    out, step = [], n_days // (n_folds + 1)
    for f in range(1, n_folds + 1):
        lo, hi = f * step, (f + 1) * step - 1
        train = df[df["day"] + H < lo]                     # labels must end before the test
        test = df[df["day"].between(lo, hi)]
        out.append(fit_score(train, test))
    return out


def purged_kfold(df, k=5):
    days = list(range(df["day"].max() + 1))
    out = []
    for block in np.array_split(days, k):
        keep = purged_train_days(days, block[0], block[-1])
        out.append(fit_score(df[df["day"].isin(keep)], df[df["day"].between(block[0], block[-1])]))
    return out


def cpcv(df, N=6, K=2):
    days = list(range(df["day"].max() + 1))
    blocks = np.array_split(days, N)
    splits = list(combinations(range(N), K))      # every pair of blocks
    paths = len(splits) * K // N
    print(f"\nCPCV: {len(splits)} splits, {paths} paths")
    per_block = {b: [] for b in range(N)}
    for split in splits:
        keep = set(days)
        for b in split:
            keep &= set(purged_train_days(days, blocks[b][0], blocks[b][-1]))
        train = df[df["day"].isin(keep)]
        m = model().fit(features(train), train[TARGET])
        for b in split:
            test = df[df["day"].between(blocks[b][0], blocks[b][-1])]
            per_block[b].append(daily_rank_ic(test, m.predict(features(test))))
    # path p uses the p-th prediction made for every block: one full honest backtest
    path_ics = [np.mean([per_block[b][p] for b in range(N)]) for p in range(paths)]
    for p, ic in enumerate(path_ics, 1):
        print(f"  path {p}: rank IC={ic:+.3f}")
    print(f"  spread across paths: {max(path_ics) - min(path_ics):.3f}  (a wide spread is a warning)")


if __name__ == "__main__":
    print("purged_train_days on 0..99, test block 40..59:")
    kept = purged_train_days(list(range(100)), 40, 59)
    print(f"  keeps {len(kept)} days: 0..{max(d for d in kept if d < 40)} and "
          f"{min(d for d in kept if d > 59)}..99\n")

    df = load_panel().dropna(subset=NUMERIC + [TARGET]).reset_index(drop=True)
    dates = sorted(df["date"].unique())
    df["day"] = df["date"].map({d: i for i, d in enumerate(dates)})   # days as simple numbers
    print(f"panel: {len(df)} rows, {df['fund'].nunique()} funds, {len(dates)} days "
          f"(horizon {H}d, embargo {EMBARGO}d)\n")
    report("shuffled K-fold (leaky)", shuffled_cv(df))
    report("walk-forward", walk_forward(df))
    report("purged + embargoed K-fold", purged_kfold(df))
    print("\nIf the leaky score is much higher, the gap is leakage, not skill.")
    cpcv(df)
