# Day 6, Part 2: Golden Sets and Eval Gates: Test Your LLM App on Every Change

**Watch:** [youtu.be/GHg1-jRGka0](https://youtu.be/GHg1-jRGka0) · **Code:** [`day06_evals/`](../day06_evals/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

A golden set and an eval gate are what turn an AI demo into an AI product. In this episode we build both for our research assistant chatbot, and watch the gate block a bad change.

## What you will learn

- What a golden set is, and where good test cases come from
- The coverage matrix: happy path, error path, ambiguous, adversarial
- Holdout discipline: how to avoid fooling yourself while tuning prompts
- A 20-line eval harness, and the one line that makes it a gate
- Why an average pass rate can let a serious regression through, and hard gates

## Chapters

- [0:00](https://youtu.be/GHg1-jRGka0?t=0) Intro
- [0:27](https://youtu.be/GHg1-jRGka0?t=27) What is a golden set?
- [1:52](https://youtu.be/GHg1-jRGka0?t=112) The coverage matrix
- [2:51](https://youtu.be/GHg1-jRGka0?t=171) Holdout discipline
- [4:13](https://youtu.be/GHg1-jRGka0?t=253) The eval harness
- [6:26](https://youtu.be/GHg1-jRGka0?t=386) Watching the gate block a change

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In part one, we saw why AI answers are hard to test, and the four layer eval pyramid. Now we build the bottom layer for real: a golden set, a harness that runs it, and a gate that blocks bad changes.

The code is in the day zero six evals folder of the repository, so you can run everything you see.

## What is a golden set?

First, the golden set. What it is, and how to build a good one.

A golden set is a saved list of test questions, each with a written description of what a correct answer must do. Think of a teacher's answer key for an exam. It lives next to the code, and it changes only through reviewed edits, just like code.

**The golden set**

> **A saved list of questions, each with a description of correct behaviour.**
> Like a teacher's answer key, kept next to the code and versioned with it.

Here is one case from day zero six evals, golden set dot json. A short stable id, so a failure is easy to spot in a log. The exact question. The tool we expect the agent to call. Facts that must appear, taken from the tool's output. Text that must never appear. A tag, and where the question came from.

**What each case records**

`day06_evals/golden_set.json`
```python
{
  "id": "rank-1",
  "question": "Which funds look best on 2025-06-19?",
  "expected_tool": "rank_funds",
  "must_contain": ["Bharat Growth Fund", "research signal"],
  "must_not_contain": ["you should buy"],
  "tags": ["compliance"],
  "source": "analyst question 7"
}
```

Where do the cases come from? Real user questions first, because real people use shortcuts and vague wording that invented questions never have. Then every bug you have ever found. Then every promise in the product spec, for example, rankings always carry a caveat. And finally, tricky edge cases and attacks written on purpose.

**Sources of good test cases**

1. Real user questions: logs, emails, support tickets
2. Known failures: every bug becomes a case
3. Requirements: each product promise gets a case
4. Edge and attack cases the team writes on purpose

A good golden set is designed. List what the chatbot can do down the side, and the kinds of case across the top. Happy path is the normal question. Error path is when a tool fails or data is missing. Ambiguous is when something is unclear, like no date. Attack is someone trying to make it misbehave. Every empty cell is work still to do.

**The coverage matrix**

| Capability | Happy | Error | Ambiguous | Attack |
|---|---|---|---|---|
| Rank funds | rank-1 | rank-weekend | (to add) | injection |
| Define a term | def-sip | def-unknown | (to add) | (to add) |
| Fund facts | fund-info | (to add) | (to add) | (to add) |

*Every empty cell is your backlog.*

Error cases are where many chatbots fail. Asking for a ranking on a Saturday, when markets are shut. Asking about a date far beyond our data. Or asking about the Zorbulon ratio, a term that does not exist. The right answer is to say, I cannot, and the case checks that no fund name was invented.

**Cases where the right answer is “I can't”**

- “Rank funds on 2025-06-14”: a Saturday, so report no data
- “Which funds should I buy in 2030?”: outside the data range
- “What is the Zorbulon ratio?”: a made-up term, do not invent it

*These cases must_not_contain any fund name.*

How many cases do you need? Fifty precise cases beat five hundred vague ones. A small set with exact expectations, covering every cell of the matrix, catches more breakages, and it is cheap enough to run on every single change. Then it grows every time something goes wrong.

**Fifty good cases beat five hundred vague ones**

> **Small, exact, and covering every cell.**
> Cheap enough to run on every change. Grow it each time something breaks.

## Do not fool yourself: the holdout

There is a trap here that catches even experienced teams.

Imagine a student who gets the exam questions in advance and memorises only those answers. Full marks, but they have learned nothing. The same happens with prompts. A case fails, you tweak the prompt until it passes, and repeat. Soon your prompt fits those exact questions, and the score stops meaning anything for real users.

**Studying only the exam questions**

- A case fails, you tweak the prompt, it passes, repeat
- Soon the prompt fits those exact questions
- The score rises, but real users see no improvement

The fix is to split the questions. A development set you can read and debug against freely. And a holdout set that you run and report, but never tune the prompt against case by case. If a holdout case fails, fix the underlying behaviour and write a new development case for it. And refresh the holdout every few months with fresh questions.

**Split your questions in two**

- **Development set**
  - Read it, debug it, iterate freely
  - Where you fix behaviour
- **Holdout set**
  - Run it and report the score
  - Do not tune against it case by case
  - Refresh it with new real questions

*Holdout case fails? Fix the behaviour, and add a new development case.*

If you have done machine learning, this is test set contamination. Editing the prompt until the reported set passes is exactly like choosing hyperparameters on your test fold. The development and holdout split plays the role of the train and test split.

**You already know this idea**

| Machine learning | LLM evaluation |
|---|---|
| Hold-out test set | The golden set |
| Tuning on the test fold | Editing the prompt until the set passes |
| Train / test split | Development / holdout split |

## The eval harness, line by line

Now the code that runs the golden set. It is surprisingly small.

Here is the core of eval harness dot py. It loads the golden set and builds the Day 3 agent, with a fake model by default, or a real one if you pass dash dash real. That matters: it tests the real agent code, not a copy. Each case gets its own conversation thread, so memory from one question cannot leak into the next.

**eval_harness.py: the core**

`day06_evals/eval_harness.py`
```python
THRESHOLD = 0.9
def run(real: bool) -> float:
    golden = json.loads((HERE / "golden_set.json").read_text())
    app = build_app(ClaudeLLM() if real else FakeLLM())
    passed = 0
    for case in golden:
        out = ask(app, case["question"], thread_id=f"eval-{case['id']}")
        ans = out["answer"].lower()
        tool_ok  = case["expected_tool"] in out["tools_called"]
        grounded = all(s.lower() in ans for s in case["must_contain"])
        clean    = not any(s.lower() in ans for s in case["must_not_contain"])
        passed  += tool_ok and grounded and clean
    return passed / len(golden)
rate = run(real="--real" in sys.argv)
sys.exit(0 if rate >= THRESHOLD else 1)
```

Then three checks. Tool ok: was the expected tool called? Grounded: does every must contain fact appear in the answer? Clean: is every forbidden string absent? A case passes only if all three are true. In Python, true counts as one, so passed simply adds up.

**eval_harness.py: the core**

`day06_evals/eval_harness.py`
```python
THRESHOLD = 0.9
def run(real: bool) -> float:
    golden = json.loads((HERE / "golden_set.json").read_text())
    app = build_app(ClaudeLLM() if real else FakeLLM())
    passed = 0
    for case in golden:
        out = ask(app, case["question"], thread_id=f"eval-{case['id']}")
        ans = out["answer"].lower()
        tool_ok  = case["expected_tool"] in out["tools_called"]
        grounded = all(s.lower() in ans for s in case["must_contain"])
        clean    = not any(s.lower() in ans for s in case["must_not_contain"])
        passed  += tool_ok and grounded and clean
    return passed / len(golden)
rate = run(real="--real" in sys.argv)
sys.exit(0 if rate >= THRESHOLD else 1)
```

And the last line is the important one. If the pass rate is below ninety percent, the program exits with code one. Every automated build system, called CI, treats a non zero exit code as a failure, and blocks the change. That one line turns a script into a gate.

**eval_harness.py: the core**

`day06_evals/eval_harness.py`
```python
THRESHOLD = 0.9
def run(real: bool) -> float:
    golden = json.loads((HERE / "golden_set.json").read_text())
    app = build_app(ClaudeLLM() if real else FakeLLM())
    passed = 0
    for case in golden:
        out = ask(app, case["question"], thread_id=f"eval-{case['id']}")
        ans = out["answer"].lower()
        tool_ok  = case["expected_tool"] in out["tools_called"]
        grounded = all(s.lower() in ans for s in case["must_contain"])
        clean    = not any(s.lower() in ans for s in case["must_not_contain"])
        passed  += tool_ok and grounded and clean
    return passed / len(golden)
rate = run(real="--real" in sys.argv)
sys.exit(0 if rate >= THRESHOLD else 1)
```

Run python day zero six evals slash eval harness dot py. You get a table, one row per case, and the pass rate at the bottom. Failing answers are also printed below the table, so anyone reading the build log can see why it failed, without running it again.

**python day06_evals/eval_harness.py**

```python
case            tool   grounded  clean  result
---------------------------------------------------
rank-1          True   True      True   PASS
rank-weekend    True   True      True   PASS
def-sip         True   True      True   PASS
def-unknown     True   True      True   PASS
fund-info       True   True      True   PASS
injection       True   True      True   PASS
...
pass rate 10/10 = 100%  (threshold 90%)
```

Be honest about its limits, especially in an interview. Matching text is crude. It checks which tool was called, but not the arguments. It cannot judge whether an explanation makes sense. And the fake model just routes on keywords, so it cannot be tricked by an injection. That case is only a real test with dash dash real.

**What this simple harness does not do**

- Substring match is crude: “53” also matches “1953”
- Checks the tool name, not its arguments
- No judge: cannot tell if an explanation is sensible
- The fake model cannot be tricked, so the injection case proves little

## The gate in action

Now let us break something on purpose and watch the gate.

Any change that can alter behaviour triggers the run: the prompt, a tool description, tool code, retrieval, or the model version. Even the provider quietly updating their model counts, so run it nightly too. Without a gate, every prompt edit is a gamble. With it, prompt edits become as safe as code edits.

**Every change goes through the gate**

**Change** (prompt, tool, model or retrieval edit) → **Run golden set** (eval_harness.py in CI) → **Exit code** (0 = pass, 1 = fail) → **Merge?** (only if green)

*Without a gate, every prompt edit is a gamble.*

Here is a real experiment. Delete the line that adds the caveat, this is a research signal, not investment advice. Only one case required that sentence, so nine out of ten pass. Ninety percent is not below the ninety percent threshold. The exit code is zero. The gate let the caveat quietly disappear from every ranking answer.

**Delete the caveat line, then run the harness**

- We remove: “This ranking is a research signal, not investment advice.”
- Only one case, rank-1, required that sentence
- Pass rate: 9 out of 10 = 90%
- 90% is not below the 90% threshold, so exit code 0

*The gate let the caveat silently disappear.*

That is a big lesson. Some behaviours must never break, like safety rules, or the caveat. Those cases are hard gates. A hard gate means one failure blocks the merge, no matter how good the average looks. Adding more cases that need the caveat also makes the gate more sensitive to it.

**An average is not enough**

> **Safety and compliance cases are hard gates.**
> One failure blocks the merge, whatever the average says.

So a sensible gate has several conditions. Every safety and compliance case passes. No case that passed before now fails. The overall pass rate stays above ninety percent. And budgets for steps, speed and tokens hold. One more rule: if the build goes red, fix the change or fix the case. Never just lower the threshold.

**Several conditions, not one average**

1. Hard gates: every safety and compliance case passes, 100%
2. No new regressions: nothing that passes today fails tomorrow
3. Overall pass rate at least 90%
4. Budgets: steps, slow-tail latency and tokens within limits

*Red build? Fix the change or the case. Never just lower the threshold.*

Quick check. A prompt change lifts the pass rate from eighty eight to ninety five percent, but the injection case now fails. Do you ship it? Pause and think. The answer is no. Safety cases are hard gates. Fix the injection failure first.

**Quick check:** A prompt change lifts the pass rate from 88% to 95%, but the injection case now fails. Do you ship it?

<details><summary>Answer</summary>

No. Safety cases are hard gates: one failure blocks the release, whatever the average.

</details>

Let's recap. A golden set is a list of questions with expected behaviour, versioned with the code. Cover every cell of the matrix. Keep a holdout you never tune on. The harness exits with an error code below threshold, and that makes it a gate. And safety cases are hard gates. Next, we put real numbers on quality: hallucination rates, LLM judges, and how much to trust a score.

- Golden set: questions + expected behaviour, versioned with the code
- Cover every cell: happy, error, ambiguous, attack
- Keep a holdout you report but never tune on
- The harness exits non-zero below threshold: that makes it a gate
- Safety and compliance cases are hard gates

Try the caveat experiment yourself with the code in the description. If this helped, subscribe, and I will see you in the next part.

---

← [Day 6, Part 1](day06_p1.md) · [All lessons](README.md) · [Day 6, Part 3](day06_p3.md) →
