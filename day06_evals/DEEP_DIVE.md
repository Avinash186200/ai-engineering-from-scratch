# Day 6 deep dive: evaluating an LLM product

Read after the Day 6 episodes. Code: `eval_harness.py` (the CI gate) and `eval_stats.py` (how sure you can be).

## 1. Why classic metrics are not enough

A regression model gives you one number per row and a held-out test set. An LLM product gives you free text,
several steps (route, call a tool, read the result, write), and a cost per request. So you measure each step,
not just the final answer, and you accept that some checks are fuzzy.

## 2. Four layers of evaluation

| Layer | What it checks | Speed and cost | Example |
|---|---|---|---|
| Deterministic checks | Things code can verify exactly | Fast, free, runs on every commit | Right tool called, JSON valid, number in the answer equals the tool output, banned string absent |
| LLM as judge | Things that need reading | Seconds, costs tokens | "Is every claim supported by the retrieved passage?" scored 1-5 against a rubric |
| Human review | Calibration and edge cases | Slow, expensive | Weekly sample of 50 traces scored by a domain expert |
| Online signals | What real users experience | Continuous | Thumbs up/down, retries, abandoned sessions, escalations |

Put as much as possible in the first layer. Use the judge only where code cannot decide, and check the judge
against humans.

## 3. What to measure for an agent

- **Task success**: did the user get a correct, complete answer? The headline number.
- **Tool selection accuracy**: right tool for the question. Count wrong-tool and missed-tool separately.
- **Argument correctness**: right tool, right inputs (date, entity, units). A common silent failure.
- **Groundedness**: share of claims backed by a tool result or retrieved text.
- **Refusal correctness**: refuses what it should (advice, out of scope), answers what it should.
- **Latency**: report p50 and p95, never just the mean. A few slow tool calls hide in an average.
- **Cost per completed task**: total token spend divided by tasks that succeeded, so retries and failures count.

Worked cost example: 1,000 requests, average 3,000 input and 400 output tokens, prices of 3 and 15 per million.
Input: 1,000 x 3,000 x 3 / 1e6 = 9.0. Output: 1,000 x 400 x 15 / 1e6 = 6.0. Total 15.0. If 850 tasks succeed,
cost per completed task is 15.0 / 850 = about 0.018, not 0.015.

## 4. Building a golden set

- **Sources**: real user questions (best), questions from domain experts, known past failures, and adversarial cases
  (injection, out-of-scope, bad dates).
- **Coverage matrix**: list the intents (rank, define, compare, refuse) against the conditions (normal, edge,
  error, attack). Every cell gets at least one case.
- **Each case records**: the input, the expected tool and arguments, facts the answer must contain, strings it
  must not contain, and a note on why the case exists.
- **Size**: start with 30-50 so it runs in CI. Grow towards a few hundred for release decisions.
- **Holdout**: keep a slice you never tune prompts against, or you overfit the golden set like any test set.
- **Every bug becomes a case**: a production failure that is fixed without a new case can come back.

## 5. LLM as judge

- **Rubric**: one property per judge (groundedness, tone, completeness), with an anchored scale ("5 = every claim
  cited; 3 = one unsupported claim; 1 = invented facts").
- **Pointwise vs pairwise**: pointwise scores one answer; pairwise asks "A or B?" and is more stable when
  comparing two prompt versions.
- **Known biases**: prefers the first option shown (swap the order and average), prefers longer answers,
  prefers its own model family, and is lenient on fluent but wrong text.
- **Calibration**: label 100 cases by hand, run the judge, and measure agreement (accuracy or Cohen's kappa).
  If agreement is low, fix the rubric before trusting the score.

## 6. Statistical care (`eval_stats.py`)

- **A pass rate is an estimate.** 10 out of 10 gives a 95% Wilson range of about 72% to 100%. Quote the range.
- **Compare on the same cases.** Only the cases where the two versions disagree tell you anything. A sign test on
  those disagreements says whether the gap is real. In the demo, 40/50 versus 46/50 is still not clearly different.
- **Flaky cases**: run each case 3 times at the production temperature. A case that passes 2 of 3 is a finding,
  not noise to hide.

## 7. Evals as a deploy gate

- **Triggers**: any change to a prompt, a tool description, the model name, retrieval settings or the agent graph.
- **Threshold**: a fixed bar (here 90%) plus "no case that passed on main may now fail" for critical cases.
- **Three outcomes**: pass, fail, or unsure (the range straddles the bar). Unsure means add cases, not ship.
- **What a gate does not do**: it does not prove the product is good. It only stops known regressions.
  Online signals and human review find the new failures.

## Interview lines

- "I evaluate each step: routing, tool arguments, grounding, then the final answer."
- "Our golden set has a coverage matrix and a holdout, and every production bug becomes a case."
- "I report the pass rate with its interval, and compare versions with a paired test on the same cases."
