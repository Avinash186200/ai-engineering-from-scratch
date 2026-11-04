# Day 7, Part 4: Combinatorial Purged CV, Deflated Sharpe and PBO Explained

**Watch:** [youtu.be/6KIUmIWWHMQ](https://youtu.be/6KIUmIWWHMQ) · **Code:** [`day07_ml/`](../day07_ml/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

You tried ten model variants and kept the best one. Is it actually good, or just the luckiest? In this episode we use our synthetic fund-ranking model to learn combinatorial purged cross-validation, the multiple-testing trap, the deflated Sharpe ratio and the probability of backtest overfitting (PBO).

## What you will learn

- Combinatorial purged cross-validation (CPCV): many test paths instead of one
- Why trying many variants turns luck into apparent skill
- The Sharpe ratio, and the best Sharpe you'd expect from pure luck
- The deflated Sharpe ratio, in plain words
- PBO: how often the in-sample winner loses out of sample
- How to tell an honest validation story in an interview

## Chapters

- [0:00](https://youtu.be/6KIUmIWWHMQ?t=0) Intro
- [0:18](https://youtu.be/6KIUmIWWHMQ?t=18) Many paths, not one: CPCV
- [2:08](https://youtu.be/6KIUmIWWHMQ?t=128) The trap of trying many things
- [3:27](https://youtu.be/6KIUmIWWHMQ?t=207) The deflated Sharpe ratio
- [5:44](https://youtu.be/6KIUmIWWHMQ?t=344) PBO: does the winner keep winning?
- [6:52](https://youtu.be/6KIUmIWWHMQ?t=412) After launch, and the interview story

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In the last video, we learned to test honestly with walk-forward, purging and embargo. Today, the last trap, and the one that catches even careful people: trying many models and keeping the best.

## Many paths, not one: CPCV

First, let's fix walk-forward's weakness: it gives you only one path through history.

One walk-forward run is like judging a batter on one season. They might have had a lucky year. You trust a player more when you see many seasons. Combinatorial purged cross validation, or C P C V, gives us many seasons from the same history.

**One path is one roll of the dice**

> **One test series = one season of cricket.**
> A batter can have one great season by luck. You trust an average across many seasons.

Here is how. Cut the timeline into blocks, say six, keeping them in order. Then pick every possible pair of blocks as the test set. Train on the other four, with purging and embargo at every edge. Finally, stitch the test results back together into many complete backtest paths.

**Combinatorial purged cross-validation**

1. Cut the timeline into N blocks, in order (say N = 6)
2. Pick every combination of k blocks as the test set (say k = 2)
3. Train on the rest, with purging and embargo at every edge
4. Stitch the test results back into many full backtest paths

Let's count. With six blocks and two test blocks, there are fifteen ways to choose the pair. Each split tests two blocks, so thirty block tests, and each full path needs all six blocks. Thirty divided by six gives five complete paths. Instead of one season, you now see five, and can look at their spread.

**CPCV with 6 blocks**

| Test blocks k | Train / test splits | Full paths |
|---|---|---|
| 1 | 6 | 1  (ordinary k-fold style) |
| 2 | 15 | 5 |
| 3 | 20 | 10 |

*Paths = splits x k / N.  With k = 2: 15 x 2 / 6 = 5.*

You can count this yourself. Python's combinations function lists every pair of blocks. Fifteen splits, five paths. In train ranker dot py, each split is trained with the purging and embargo from the last video, so you get five honest backtests. If their results vary wildly, that spread is itself a warning sign.

**Counting CPCV splits and paths**

`day07_ml/train_ranker.py`
```python
from itertools import combinations

N, K = 6, 2                                   # 6 blocks, 2 test blocks
splits = list(combinations(range(N), K))      # every pair of blocks
paths = len(splits) * K // N
print(len(splits), "splits,", paths, "paths")
# 15 splits, 5 paths
```

## The trap of trying many things

Now the big trap. What happens when you try many model variants and report the best one?

Ask a hundred people to toss a coin ten times each. Almost certainly, someone gets eight heads or more. Do they have a special skill? No. If you pick the best of many tries, you mostly pick the luckiest. Model variants work exactly the same way.

**A hundred people tossing coins**

> **Ask 100 people to toss a coin 10 times.**
> Someone will get 8 or more heads. That doesn't make them a skilled tosser. Pick the best of many, and you pick luck.

Here is the maths. Say each test has a five percent chance of a false alarm. Test one useless variant, and you get fooled five percent of the time. With five variants, twenty three percent. With ten, forty percent. With twenty, sixty four percent. Trying more things turns noise into apparent skill.

**Chance of at least one false “win”**

- 1 variant: 5%
- 5 variants: 23%
- 10 variants: 40%
- 20 variants: 64%

*Each test has a 5% false-alarm rate. Variants have no real skill.*

And a try is not just a model type. Every setting you tuned counts, every feature set, even the ideas you quietly dropped because they looked bad. So keep a written log of every trial. That count is exactly what the next tool needs.

**What counts as a “try”?**

- Every model type you tested
- Every setting you tuned: penalty, features, horizon
- Every idea you dropped because it looked bad

*Write down every trial. The count goes into the next formula.*

## The deflated Sharpe ratio

To correct for many tries, we need two ideas: the Sharpe ratio, and how high it goes by luck alone.

The Sharpe ratio is the average return divided by how much the returns jump around. It is return per unit of risk. If two funds both earn twelve percent a year, the one with the smoother ride has the higher Sharpe. Higher is better.

**The Sharpe ratio**

> **Sharpe = average return ÷ how much it jumps around**
> Return per unit of risk. Two funds both earn 12%: the one with the smoother ride has the higher Sharpe.

Now, imagine variants with no skill at all, whose Sharpe varies by about point five just from noise. The best of five is expected around point five eight. The best of ten, about point seven seven. The best of a thousand, over one point six. With zero real skill. These numbers are illustrative, but the shape is the lesson: more tries, higher lucky best.

**Best Sharpe expected from pure luck**

- 5 tries: 0.58
- 10 tries: 0.77
- 100 tries: 1.25
- 1,000 tries: 1.62

*Made-up spread: useless variants whose Sharpe varies by 0.5.*

The deflated Sharpe ratio raises the bar. Instead of asking, is the Sharpe above zero, it asks, is it above the best you would expect from luck, given how many tries you made? It also accounts for how long the test was and for unusual returns. The result is a probability. We usually want ninety five percent or more.

**Deflated Sharpe: raise the bar**

- **Old bar**
  - Is the Sharpe above zero?
  - Ignores how many tries
- **Deflated bar**
  - Is it above the lucky best?
  - Accounts for tries, test length, odd returns

*Deflated Sharpe = chance the true Sharpe beats the lucky best.*

Let's apply it to an illustrative example. We tried ten variants of our fund model. The best had a Sharpe of point seven. Looks decent. But the lucky best for ten tries is point seven seven. Our winner did not even beat luck. Whenever that happens, the deflated Sharpe is below fifty percent, nowhere near ninety five.

**Our fund model: ten variants**

| Quantity | Value |
|---|---|
| Variants tried | 10 |
| Best variant's Sharpe | 0.70 |
| Lucky best for 10 tries | 0.77 |
| Margin | minus 0.07 |

*Below the lucky bar → deflated Sharpe under 50%. No evidence of skill.*

Be precise about what this means. It does not prove the model is worthless. It says the backtest alone gives no statistical evidence of skill, beyond the luck of picking the best of ten. Interviewers love candidates who can say that sentence calmly.

**What that result means**

> **Not “the model is worthless”.**
> It means: this backtest alone gives no statistical evidence of skill beyond the luck of picking the best of ten.

## PBO: does the winner keep winning?

The second tool asks a different question. If I pick the winner on one half of history, does it still win on the other half?

Here is how P B O, the probability of backtest overfitting, works. Cut history into blocks, say six. Try every way of picking three as the in-sample half: there are twenty. In each, find the best variant on that half. Then check: on the other half, is it below the median? P B O is the share of splits where the winner fell below the middle.

**Probability of backtest overfitting**

1. Cut history into blocks, say 6
2. Every way to pick half as “in-sample”: 20 ways for 6 blocks
3. Find the best variant on the in-sample half
4. Is it below the median on the other half?
5. PBO = share of splits where the winner fell below median

How to read it. Fifty percent means picking the in-sample winner is no better than picking at random. Lower is healthy. In our illustrative example, P B O is seventy percent. Seven times in ten, the variant that looked best was below median on new data. Choosing a variant by backtest here is unreliable.

**Reading PBO**

- Our 10 variants: 70%
- Coin flip: 50%
- Healthy: 20%

*Above 50%: picking by backtest is worse than picking at random.*

## After launch, and the interview story

Two last things: watching the model after launch, and telling this story in an interview.

Even a validated model can fail when the world changes. Watch the inputs: do today's features look unlike the training data? Watch the outputs: has the ranking suddenly changed? Real performance arrives only twenty days later, because that is the prediction horizon. So input and output drift are your early warning signs.

**Monitor for drift**

- Input drift: are today's features unlike the training data?
- Output drift: is the ranking suddenly very different?
- Performance: real returns arrive only 20 days later
- So input and output drift are your early warnings

In an interview, tell it in five beats. I checked every feature for leakage. I tested with purged, embargoed C P C V. I logged every variant and corrected for the number of tries. I reported the deflated Sharpe and P B O, even when they disappointed. And I shipped with monitoring and clear caveats. Honesty about a weak result is a strength.

**An honest validation story**

1. Checked every feature for leakage and point-in-time dates
2. Tested with purged, embargoed CPCV, not shuffled k-fold
3. Logged every variant tried, and corrected for it
4. Reported deflated Sharpe and PBO, even when they disappointed
5. Shipped with drift monitoring and clear caveats

Final check. You tried twenty variants. The best has a Sharpe of point nine, but the lucky best for twenty tries is one point zero. What do you conclude? Pause. The answer: it did not beat luck, so the deflated Sharpe is below fifty percent. The backtest gives no evidence of skill.

**Quick check:** You tried 20 variants. The best has Sharpe 0.9, but the lucky best for 20 tries is 1.0. What do you conclude?

<details><summary>Answer</summary>

It did not beat luck: deflated Sharpe is below 50%. The backtest gives no evidence of skill.

</details>

Recap. C P C V gives many test paths instead of one. More tries mean a higher best result from luck alone. The deflated Sharpe asks if your winner beats that lucky best. P B O asks if the winner keeps winning on new data. And after launch, you monitor drift. That completes Day 7. Next, Day 8: taking our chatbot to production.

- CPCV: test every combination of blocks to get many paths, not one
- More tries means a higher best result from luck alone
- Deflated Sharpe: is the winner above the lucky best?
- PBO: how often the in-sample winner falls below median later
- Monitor drift; tell the validation story honestly

The code for Day 7 is in the day seven folder, linked in the description. If this helped, subscribe, and I will see you on Day 8.

---

← [Day 7, Part 3](day07_p3.md) · [All lessons](README.md) · [Day 8, Part 1](day08_p1.md) →
