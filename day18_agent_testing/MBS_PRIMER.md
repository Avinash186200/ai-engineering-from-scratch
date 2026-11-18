# MBS and fixed-income primer for evaluating agents

You do not need to trade. You need enough to judge if an answer is sensible, grounded and current. Read this page,
ask the analysts, and keep the glossary open while you review answers.

## Explainer

**Bond basics**

- **Coupon**: the interest rate the bond pays on its face value. A "5.5 coupon" pays 5.5% of face value a year.
- **Price and yield** move in opposite directions. Price up, yield down.
- **Basis point (bp)**: 0.01%. 100 bp = 1%.
- **Duration**: the approximate % change in price for a 1% (100 bp) change in yield, in the opposite direction.
  Duration 6 means: if yields rise 100 bp, the price falls about 6%; if yields fall 100 bp, it rises about 6%.
  Per basis point, that is about 0.06% of price. It is a first-order estimate and works best for small moves.
  Higher duration, more rate risk.
- **Convexity**: how duration itself changes as yields move. It is the correction to the duration estimate for
  larger moves. A plain bond has **positive convexity**: when yields fall its price rises a bit more than duration
  predicts, and when yields rise its price falls a bit less.
- **Spread**: extra yield over a benchmark (usually Treasuries or swaps), in bp. All else equal, a wider spread
  means a lower price relative to the benchmark; a tighter spread means a higher price.

**MBS basics**

- A **mortgage-backed security** is a bond backed by a pool of home loans. Borrowers' monthly payments of interest
  and principal flow to investors.
- **Prepayment**: borrowers can pay off early (refinance, move house). Investors then get principal back sooner than
  planned. When rates fall, refinancing makes prepayments rise. When rates rise, prepayments slow down.
- **CPR (conditional prepayment rate)**: an annualised rate. CPR 10 means about 10% of the remaining balance is
  expected to prepay over a year, at the current monthly pace. It is a percentage, never basis points.
- **Negative convexity**: because prepayments change with rates, most MBS have negative convexity. When rates fall,
  prepayments speed up, the expected life shortens, and the price rises *less* than a plain bond's (the price is
  capped near the level where refinancing takes off). When rates rise, prepayments slow, the expected life gets
  longer (**extension risk**), duration rises, and the price falls *more* than duration alone suggests.
  So for MBS, the simple duration estimate is least reliable in exactly the big moves that matter most.
- **Effective duration**: duration measured with a prepayment model, by shifting rates up and down and repricing.
  For MBS it is the right measure, and it changes as rates move. A negative **effective convexity** number (like
  the lab's -1.09) is the sign of negative convexity.
- **OAS (option-adjusted spread)**: the spread over the benchmark curve after removing the value of the borrowers'
  prepayment option (typically computed by averaging across simulated rate paths). It is model-dependent: different prepayment and
  rate models give different OAS. Always tie an OAS to its model and its date.
- **TBA (to-be-announced)**: the main forward market for agency MBS. A trade agrees the issuer program, coupon,
  term, face amount, price and settlement date, but not the exact pools. The seller picks pools that meet the
  delivery rules shortly before settlement, so sellers tend to deliver the least valuable pools allowed.
- **Cohort**: a group of loans or pools with shared traits (e.g. 30-year term, 5.5 coupon, a given origination year).
  Analysts often ask about cohorts, not single pools.

**Snapshot date and outlooks**

- A **snapshot date** (as-of date) is the date the data and model outputs refer to. Every number the agent gives
  should be traceable to a snapshot date.
- A complete snapshot and a **partial load** are different things. In the lab, 2026-11-13 is the last complete
  snapshot (5 days old, so not fresh) and 2026-11-14 is a partial load that is still filling in. "Latest" must mean
  the latest *complete* snapshot. Answering from a partial load by mistake is the bug the lab is built around.
- "Latest" may lag today by a business day or more. Weekends and holidays have no new snapshot.
- A **5-day / 21-day outlook** is a model's view over about 5 or 21 trading days (roughly one week and one month)
  from the as-of date. In the lab it returns the expected change in rates and spreads in bp, plus a confidence.
  An outlook as of 2026-11-13 and one as of 2026-11-14 are different forecasts: the lab's 5-day outlook says rates
  -2.4 bp on the 13th and +1.7 bp on the 14th. Mixing them is a real error, and the answer still reads fine.

## What evaluators check in an answer

- The as-of date is stated, matches the tool output, and is the date the user asked for (or the last complete
  snapshot), never a partial load.
- Units are right (bp vs %, CPR as an annual %, duration in years or "% per 100 bp").
- Direction words match the numbers (spread up = wider; a negative rate change = rates down).
- The model name is given for model-dependent numbers (OAS, effective duration, outlooks).
- No number appears that is not in a tool output.

## Worked example (lab values)

Agent reply: "As of 2026-11-13, POOL-A30 has an OAS of 47.6 bp, 0.6 bp tighter than on 2026-11-12. Its effective
duration is 5.87 and its convexity is -1.09."

Check against the trace: `get_bond_metrics(POOL-A30, 2026-11-13)` returned `oas_bp: 47.6, eff_duration: 5.87,
convexity: -1.09`, and `get_bond_metrics(POOL-A30, 2026-11-12)` returned `oas_bp: 48.2`. 48.2 to 47.6 is a 0.6 bp
fall, so "tighter" is right. Every number is grounded and the date matches. Pass.

What it means: a 100 bp rise in yields would cut the price by roughly 5.9%, and because convexity is negative, the
real fall for a large rise would be somewhat bigger than that.

## Exercise

Spot the errors: "As of the latest snapshot, CPR is 0.12 bp, OAS widened from 70 to 65 bp, and an effective duration
of 5.87 means the price moves 5.87 bp for every 1 bp move in yield."

**Expected answer**:
- CPR is a percentage, not bp (0.12 might mean 12% if the tool gives a fraction; check the tool output).
- 70 to 65 bp is tightening, not widening.
- Duration 5.87 means about 5.87% of price per 100 bp, or about 0.0587% of price per 1 bp, not 5.87 bp.
- "Latest snapshot" with no date: ask for the date, and check it is not a partial load.
- Check every number in the trace.

## What to show on screen

- The reply, and next to it the tool outputs it came from.
- Each number in the reply ticked against a tool output field, with its date and units.
