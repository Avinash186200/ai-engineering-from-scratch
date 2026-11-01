"""Generate a reproducible synthetic panel of Indian mutual funds.

Everything here is made up. The numbers look plausible, but no real fund is described.

Run:  python data/make_data.py      -> writes data/funds.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
OUT = Path(__file__).resolve().parent / "funds.csv"

FUNDS = [
    ("Bharat Growth Fund", "equity_large"), ("Nifty Value Fund", "equity_large"),
    ("Deccan Bond Fund", "debt"), ("Ganga Flexi Cap Fund", "equity_flexi"),
    ("Himalaya Small Cap Fund", "equity_small"), ("Konkan Liquid Fund", "debt"),
    ("Sahyadri Midcap Fund", "equity_mid"), ("Kaveri Balanced Fund", "hybrid"),
    ("Narmada Dividend Yield Fund", "equity_large"), ("Thar Infrastructure Fund", "equity_mid"),
    ("Malabar Gilt Fund", "debt"), ("Vindhya Focused Fund", "equity_flexi"),
    ("Godavari Tax Saver Fund", "equity_flexi"), ("Ajanta Bluechip Fund", "equity_large"),
    ("Coromandel Short Term Fund", "debt"), ("Aravalli Emerging Fund", "equity_small"),
    ("Brahmaputra Hybrid Fund", "hybrid"), ("Sundarban Consumption Fund", "equity_mid"),
    ("Nilgiri Index Fund", "equity_large"), ("Satpura Corporate Bond Fund", "debt"),
    ("Yamuna Multi Cap Fund", "equity_flexi"), ("Kanha Pharma Fund", "equity_mid"),
    ("Mahanadi Equity Savings Fund", "hybrid"), ("Chola Banking Fund", "equity_large"),
    ("Rann Technology Fund", "equity_mid"), ("Pench Micro Cap Fund", "equity_small"),
    ("Kosi Dynamic Bond Fund", "debt"), ("Tapti Arbitrage Fund", "hybrid"),
    ("Lakshadweep ESG Fund", "equity_flexi"), ("Shivalik Quant Fund", "equity_mid"),
]
CAT_VOL = {"debt": 0.003, "hybrid": 0.006, "equity_large": 0.010,
           "equity_flexi": 0.011, "equity_mid": 0.013, "equity_small": 0.016}
FEATURES = ["momentum_3m", "volatility_3m", "expense_ratio", "aum_cr", "fund_age_yrs", "category"]


def make_panel(seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2023-01-02", "2024-12-31")
    n = len(dates)
    market = rng.normal(0.0004, 0.009, n)                       # one common market factor
    rows = []
    for name, cat in FUNDS:
        vol = CAT_VOL[cat]
        beta = 0.1 if cat == "debt" else rng.uniform(0.6, 1.2)
        expense = round(rng.uniform(0.2, 2.2), 2)
        aum = rng.uniform(200, 40000)
        age = rng.uniform(1, 25)
        alpha = rng.normal(0.0001, 0.0002) - expense / 100 / 252   # costs eat returns
        daily = alpha + beta * market + rng.normal(0, vol, n)
        nav = 10 * np.cumprod(1 + daily)
        s = pd.Series(nav, index=dates)
        mom = s.pct_change(63)
        volat = s.pct_change().rolling(63).std() * np.sqrt(252)
        fwd = s.shift(-21) / s - 1
        for i, d in enumerate(dates):
            rows.append({
                "date": d.date().isoformat(), "fund": name, "category": cat,
                "nav": round(nav[i], 4),
                "momentum_3m": mom.iloc[i], "volatility_3m": volat.iloc[i],
                "expense_ratio": expense, "aum_cr": round(aum * (nav[i] / 10), 1),
                "fund_age_yrs": round(age + i / 252, 2), "fwd_return_21d": fwd.iloc[i],
            })
    df = pd.DataFrame(rows).dropna(subset=["momentum_3m", "volatility_3m"])
    # Inject a learnable signal: momentum helps, high costs hurt, plus noise.
    sig = 0.15 * df["momentum_3m"] - 0.004 * df["expense_ratio"]
    df["fwd_return_21d"] = df["fwd_return_21d"] + sig + rng.normal(0, 0.005, len(df))
    for c in ["momentum_3m", "volatility_3m", "fwd_return_21d"]:
        df[c] = df[c].round(5)
    return df.reset_index(drop=True)


if __name__ == "__main__":
    df = make_panel()
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT.name}: {len(df)} rows, {df['fund'].nunique()} funds, "
          f"{df['date'].min()} .. {df['date'].max()}")
