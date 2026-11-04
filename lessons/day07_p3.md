# Day 7, Part 3: Data Leakage, Walk-Forward Validation, Purging and Embargo

**Watch:** [youtu.be/QTZUTdkPCxQ](https://youtu.be/QTZUTdkPCxQ) · **Code:** [`day07_ml/`](../day07_ml/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Why do so many impressive model backtests fall apart in real life? In this episode we use our fund-ranking model to learn the four kinds of data leakage, why ordinary k-fold cross-validation fails on time series, and how walk-forward testing, purging and embargo fix it.

## What you will learn

- Overfitting in plain words, and why noisy data makes it worse
- Data leakage: four kinds, with simple fund examples
- Point-in-time correctness: the two dates every number has
- Why shuffled k-fold cross-validation cheats on time series
- Walk-forward validation, purging and embargo

## Chapters

- [0:00](https://youtu.be/QTZUTdkPCxQ?t=0) Intro
- [0:17](https://youtu.be/QTZUTdkPCxQ?t=17) The model we are testing
- [1:10](https://youtu.be/QTZUTdkPCxQ?t=70) Overfitting in plain words
- [2:25](https://youtu.be/QTZUTdkPCxQ?t=145) Leakage: four kinds
- [5:24](https://youtu.be/QTZUTdkPCxQ?t=324) Why shuffled k-fold cheats
- [6:23](https://youtu.be/QTZUTdkPCxQ?t=383) Walk-forward, purging and embargo

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In the last video, we made language models cheaper to adapt and to run. Now we switch to the second half of Day 7: how to tell if a model really works, using our fund-ranking model.

## The model we are testing

First, a reminder of the model we are testing.

Every day, for every fund, we have some features: recent momentum, volatility, cost. The model predicts each fund's return over the next twenty trading days, and rank funds returns the top ones. Remember, all data in this series is synthetic, and every number in this video is illustrative.

**What it does**

**Each day** (features for every fund: momentum, volatility, cost) → **The model** (predicts each fund's return over the next 20 trading days) → **Ranking** (rank_funds() returns the top funds)

*All data in this series is synthetic, and all numbers are illustrative.*

To check it, we run a backtest: we replay history and see how the model would have done. Here is the problem. Getting a great looking backtest is easy. Getting a true one is hard. Small, innocent mistakes make results look far better than real life will ever be.

**A backtest is a story about the past**

> **A great backtest is easy. A true one is hard.**
> A backtest replays history to see how the model would have done. Small mistakes make it look far better than real life.

## Overfitting in plain words

The first reason results lie is overfitting.

Imagine two students. One understands the subject. The other memorised last year's question paper. On last year's paper, both score full marks. On a new paper, only the first does well. A model that memorises the random noise in its training data is overfitting.

**Memorising versus learning**

- **Learns the pattern**
  - Like a student who understands
  - Does fine on new questions
- **Memorises the noise**
  - Like a student who memorised last year's paper
  - Fails when the questions change

Fund returns are especially tricky, because most of a twenty day return is random luck. A very flexible model will happily fit that luck. So simpler, constrained models often do better on new data. Deliberately holding a model back like this is called regularisation.

**Fund returns are mostly noise**

- Most of a 20-day return is random luck
- A flexible model will happily fit that luck
- So simple, constrained models often generalise better
- Regularisation: deliberately keep the model simple

If you have done some machine learning before, this is the bias variance trade-off. With noisy data, variance is the main enemy, so penalised linear models like ridge, lasso and elastic net are sensible first choices. If this is new to you, just keep the plain meaning on the right.

**The same idea in ML terms**

| Term | Plain meaning |
|---|---|
| Bias | Error from a model too simple to see the pattern |
| Variance | Error from a model that changes with every sample |
| Ridge, lasso, elastic net | Penalise big coefficients to cut variance |

## Leakage: four kinds

The second reason, and the more dangerous one, is leakage.

Leakage means information that would not be available at prediction time sneaks into training or testing. It is like a student who saw the answer key before the exam. The score looks amazing, and means nothing. There are four kinds you should be able to name.

**What is leakage?**

> **Information from the future sneaks into training or testing.**
> Like a student who saw the answer key before the exam. The score looks amazing, and means nothing.

One, target leakage. The answer itself, or something computed from it, is left among the inputs. For example, a column called forward return twenty days, accidentally left in the feature list. The model simply reads the answer.

Two, a look-ahead feature. A feature that looks innocent, but was built using future data. Say a momentum feature that, through a coding slip, uses tomorrow's NAV. The name gives nothing away. Only reading how it was built reveals it.

Three, late arriving data. A fund's monthly factsheet describes the end of the month, but it is only published around the tenth. If the model uses it on the first, it is using data nobody had yet.

Four, overlap between training and test data. If the test days have near copies sitting in the training set, the test is no longer a real test. This one is subtle with time series, and it gets its own section in a moment.

**Four kinds of leakage**

| Kind | Fund example |
|---|---|
| Target leakage | A column “fwd_return_20d” left in the features |
| Look-ahead feature | “Momentum” built using tomorrow's NAV by mistake |
| Late-arriving data | Month-end factsheet used on the 1st; published on the 10th |
| Train-test overlap | Shuffled split: near-copies of test days in training |

The fix for late data is called point in time correctness. Every number has two dates. The reference date says what period it describes. The availability date says when anyone could first know it. A safe pipeline always joins features on the availability date.

**Point-in-time: every number has two dates**

- **Reference date**
  - What period it describes
  - e.g. factsheet for 31 March
- **Availability date**
  - When anyone could first know it
  - e.g. published 10 April

*Join features on the availability date. Always.*

One more subtle trap. Suppose the saved model was trained on all the data, and you ask it to rank funds on a date from two years ago. That model already saw what happened after that date. The output is fine for a demo, but it is not a backtest, and it is not evidence.

**In-sample is not a backtest**

> **Trained on everything, then scored on an old date?**
> That model already saw the outcome of that date. Fine for a demo, but it is not evidence. Evidence comes only from properly held-out tests.

How do you catch leaks? Start with suspicion. If a result looks too good to be true, assume a leak until you prove otherwise. Read how every feature is built, not just its name. Check each input's availability date. And try dropping the strongest feature. If the whole result collapses, look very closely at that feature.

**A leakage checklist**

- Too good to be true? Assume a leak until proven otherwise
- Read how every feature is built, not just its name
- Check each input's availability date
- Drop the top feature: does the result collapse?

## Why shuffled k-fold cheats

Now, the standard way to test a model, and why it breaks on time series.

The usual method is called k fold cross validation. Shuffle all the rows, cut them into, say, five groups called folds. Train on four, test on the fifth, and repeat so every fold gets a turn. It quietly assumes every row is independent of every other row.

**k-fold cross-validation**

- Shuffle rows, cut them into k groups called folds
- Train on k minus 1 folds, test on the one left out; repeat
- Assumes every row is independent of the others

Fund data breaks that in two ways. First, neighbours look alike: today's features are almost the same as yesterday's. Second, the answers overlap. The twenty day return starting third March and the one starting fourth March share nineteen of their twenty days. So shuffling puts near copies of the test answers into training.

**Fund data is not independent**

- **Neighbours look alike**
  - Today's features ≈ yesterday's
  - Training on 3 March nearly reveals 4 March
- **Answers overlap**
  - 20-day return from 3 March
  - and from 4 March share 19 of 20 days

*Shuffling puts near-copies of test answers in training.*

## Walk-forward, purging and embargo

So how do we test honestly? Three ideas: walk-forward, purging, and embargo.

Walk-forward is the natural fix. Train on data up to a date, test on the next block, then roll forward and repeat. You always train on the past and test on the future, just like real use. Its weakness: you get only one path through history, one draw of luck, and early rounds have little data.

**Walk-forward validation**

**Round 1** (train Jan-Jun, test Jul) → **Round 2** (train Jan-Jul, test Aug) → **Round 3** (train Jan-Aug, test Sep)

*Always train on the past, test on the future.*

*Weakness: only one path through history, and early rounds have little data.*

Even with walk-forward, the edges leak. A training row from just before the test block has a twenty day answer that runs into the test period. Purging removes those rows from training.

Embargo goes one step further. It also drops a gap of days right after each test block, because rolling features like volatility carry test period information forward. Think of a cooling off gap between two matches on the same pitch.

**Purging and embargo**

- Purging: drop training rows whose 20-day answer overlaps the test period
- Embargo: also drop a gap of days right after each test block
- Why: rolling features like volatility carry test-period information forward

*Like a cooling-off gap between two cricket matches on one pitch.*

Here is the core of it in train ranker dot py, with days as simple numbers. The two highlighted lines do the work. Drop any row whose answer window overlaps the test block, and drop any row in the embargo gap after it. Run python day07 underscore ml slash train ranker dot py to see the splits.

**A purged, embargoed split**

`day07_ml/train_ranker.py`
```python
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
```

Here is the pattern you should expect, with made up numbers. The same model scores much better under shuffled k fold than under purged walk-forward. The model did not change. Only the honesty of the test changed. The gap between the two is roughly how much the leaky test was flattering you.

**Same model, two ways to test it**

- Shuffled k-fold: 0.62
- Purged walk-fwd: 0.21

*Made-up numbers to show the pattern: leaky tests flatter the model.*

Quick check. A fund's monthly factsheet for thirty first March is published on tenth April. On what date may the model first use it? Pause and think. The answer is tenth April, the availability date. Using it any earlier is look-ahead leakage.

**Quick check:** A fund's monthly factsheet for 31 March is published on 10 April. On what date may the model first use it?

<details><summary>Answer</summary>

10 April, its availability date. Using it earlier is look-ahead leakage.

</details>

Recap. Backtests are easy to flatter, and noisy data makes overfitting likely. Know the four kinds of leakage. Join data on its availability date. Shuffled k fold cheats on time series. Walk-forward with purging and embargo gives an honest test. Next: what happens when you try many models and keep the best one.

- Backtests are easy to flatter; noisy fund data makes overfitting likely
- Four leaks: target, look-ahead feature, late data, train-test overlap
- Point-in-time: join on the availability date, not the reference date
- Shuffled k-fold cheats on time series: neighbours and answers overlap
- Walk-forward + purging + embargo give an honest test

The code is in the day seven folder, linked in the description. Subscribe, and I will see you in the next video.

---

← [Day 7, Part 2](day07_p2.md) · [All lessons](README.md) · [Day 7, Part 4](day07_p4.md) →
