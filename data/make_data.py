"""Generate a reproducible synthetic panel of Indian mutual funds.

Everything here is made up. The numbers look plausible, but no real fund is described.
The panel covers business days from 2020-01-01 to 2025-06-30, so every date used in the
videos (for example 2025-06-19 and 2025-06-20) has data, and weekends do not.

Run:  python data/make_data.py      -> writes data/funds.csv (also built on first use)
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
START, END = "2020-01-01", "2025-06-30"
WARMUP_START = "2019-09-30"         # 3 extra months so momentum exists from START
OUT = Path(__file__).resolve().parent / "funds.csv"
H = 20                       # label horizon: the target is the next 20 trading days' return
TARGET = f"fwd_return_{H}d"

# (name, category, style). Category is what users filter on; style sets the volatility.
NAMED = [
    ("Bharat Growth Fund", "equity", "large"), ("Nifty Value Fund", "equity", "large"),
    ("Deccan Bond Fund", "debt", "bond"), ("Ganga Flexi Cap Fund", "equity", "flexi"),
    ("Himalaya Small Cap Fund", "equity", "small"), ("Konkan Liquid Fund", "debt", "liquid"),
    ("Sahyadri Midcap Fund", "equity", "mid"), ("Kaveri Balanced Fund", "hybrid", "hybrid"),
    ("Narmada Dividend Yield Fund", "equity", "large"), ("Thar Infrastructure Fund", "equity", "mid"),
    ("Malabar Gilt Fund", "debt", "bond"), ("Vindhya Focused Fund", "equity", "flexi"),
    ("Godavari Tax Saver Fund", "equity", "flexi"), ("Ajanta Bluechip Fund", "equity", "large"),
    ("Coromandel Short Term Fund", "debt", "bond"), ("Aravalli Emerging Fund", "equity", "small"),
    ("Brahmaputra Hybrid Fund", "hybrid", "hybrid"), ("Sundarban Consumption Fund", "equity", "mid"),
    ("Nilgiri Index Fund", "equity", "large"), ("Satpura Corporate Bond Fund", "debt", "bond"),
    ("Yamuna Multi Cap Fund", "equity", "flexi"), ("Kanha Pharma Fund", "equity", "mid"),
    ("Mahanadi Equity Savings Fund", "hybrid", "hybrid"), ("Chola Banking Fund", "equity", "large"),
    ("Rann Technology Fund", "equity", "mid"), ("Pench Micro Cap Fund", "equity", "small"),
    ("Kosi Dynamic Bond Fund", "debt", "bond"), ("Tapti Arbitrage Fund", "hybrid", "hybrid"),
    ("Lakshadweep ESG Fund", "equity", "flexi"), ("Shivalik Quant Fund", "equity", "mid"),
]
PLACES = ["Andaman", "Bastar", "Chambal", "Dandeli", "Ellora", "Gir", "Hampi", "Indus",
          "Jaisalmer", "Kutch", "Ladakh", "Majuli", "Nalanda", "Orchha", "Palani", "Ranthambore",
          "Sanchi", "Tawang", "Udaipur", "Varkala", "Wayanad", "Zanskar", "Bhimbetka", "Agumbe"]
KINDS = [("Large Cap Fund", "equity", "large"), ("Mid Cap Fund", "equity", "mid"),
         ("Income Fund", "debt", "bond"), ("Balanced Advantage Fund", "hybrid", "hybrid")]
STYLE_VOL = {"liquid": 0.0004, "bond": 0.0015, "hybrid": 0.004, "large": 0.006,
             "flexi": 0.007, "mid": 0.008, "small": 0.010}
EXPENSE = {"Bharat Growth Fund": 0.85, "Deccan Bond Fund": 0.45, "Himalaya Small Cap Fund": 1.60}
# A few funds launched recently: on 2025-06-19 they have under 3 months of history, so the
# ranking tool reports them as "excluded" instead of scoring them.
NEW_LAUNCH = "2025-05-02"
N_NEW = 4
# A tilt that makes the story in the videos reproducible: these funds had a strong spring 2025.
SPRING_TILT = {"Bharat Growth Fund": 0.0012, "Nifty Value Fund": 0.0011, "Deccan Bond Fund": 0.0011}
TILT_START, TILT_END = "2025-03-17", "2025-06-20"


def fund_list() -> list[tuple[str, str, str]]:
    funds = list(NAMED)
    extra = [(f"{p} {k}", c, s) for p in PLACES for (k, c, s) in KINDS]
    return funds + extra[: 124 - len(funds)]              # 124 funds in total


def make_panel(seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(WARMUP_START, END)
    n = len(dates)
    market = rng.normal(0.00005, 0.004, n)                    # one common market factor
    tilt_mask = (dates >= TILT_START) & (dates <= TILT_END)
    funds = fund_list()
    new_funds = {name for name, _, _ in funds[-N_NEW:]}
    frames = []
    for name, cat, style in funds:
        vol = STYLE_VOL[style]
        beta = {"liquid": 0.0, "bond": 0.05, "hybrid": 0.5}.get(style, rng.uniform(0.7, 1.2))
        expense = EXPENSE.get(name, round(float(rng.uniform(0.2, 2.2)), 2))
        aum = rng.uniform(200, 40000)
        age = rng.uniform(1, 25)
        alpha = rng.normal(0.0001, 0.0002) - expense / 100 / 252   # costs eat returns
        daily = alpha + beta * market + rng.normal(0, vol, n)
        daily = daily + np.where(tilt_mask, SPRING_TILT.get(name, 0.0), 0.0)
        nav = pd.Series(10 * np.cumprod(1 + daily), index=dates)
        df = pd.DataFrame({
            "date": dates.strftime("%Y-%m-%d"), "fund": name, "category": cat, "style": style,
            "nav": nav.values,
            "momentum_3m": nav.pct_change(63).values,
            "volatility_3m": (nav.pct_change().rolling(63).std() * np.sqrt(252)).values,
            "expense_ratio": expense,
            "aum_cr": np.round(aum * nav.values / 10, 1),
            "fund_age_yrs": np.round(age + np.arange(n) / 252, 2),
            TARGET: (nav.shift(-H) / nav - 1).values,
        })
        if name in new_funds:                                # launched recently: young history
            df = df[df["date"] >= NEW_LAUNCH].copy()
            launched = df.index.min()
            df["fund_age_yrs"] = np.round((df.index - launched) / 252, 2)
            df["momentum_3m"] = df["nav"].pct_change(63)
            df["volatility_3m"] = df["nav"].pct_change().rolling(63).std() * np.sqrt(252)
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    # Anchor one NAV so the worked example in the videos reads the same: 48.72 on 2025-06-19.
    bg = df["fund"] == "Bharat Growth Fund"
    anchor = df.loc[bg & (df["date"] == "2025-06-19"), "nav"].iloc[0]
    df.loc[bg, "nav"] = df.loc[bg, "nav"] * (48.72 / anchor)
    df["nav"] = df["nav"].round(4)
    # Drop warm-up rows of established funds (no 3-month history yet). Young funds keep theirs.
    warm = df["momentum_3m"].isna() & ~df["fund"].isin(new_funds)
    df = df[~warm & (df["date"] >= START)].copy()
    # Inject a learnable signal: momentum helps, high costs hurt, plus noise.
    sig = 0.10 * df["momentum_3m"].fillna(0) - 0.003 * df["expense_ratio"]
    df[TARGET] = df[TARGET] + sig + rng.normal(0, 0.005, len(df))
    for c in ["momentum_3m", "volatility_3m", TARGET]:
        df[c] = df[c].round(5)
    return df.sort_values(["date", "fund"]).reset_index(drop=True)


if __name__ == "__main__":
    df = make_panel()
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT.name}: {len(df)} rows, {df['fund'].nunique()} funds, "
          f"{df['date'].min()} .. {df['date'].max()}")
