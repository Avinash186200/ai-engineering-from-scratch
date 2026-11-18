# Day 18, Part 5: Testing AI Agents: Playwright, Bug Triage, Releases

**Watch:** video coming soon · **Code:** [`day18_agent_testing/`](../day18_agent_testing/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

All agent tests are green, and the chat page is blank. This last part of Day 18 covers the browser smoke test that catches that, how to build a test corpus, how to triage failures so nothing is lost, and the release rules that keep a tested build and a shipped build the same thing.

## What you will learn

- What a UI smoke test should check, and what it should not
- The lab's Playwright test, line by line, and Playwright vs Selenium
- Making browser tests stable instead of flaky
- Where test cases come from, and why tests can be wrong too
- Triage: one row per root cause; release discipline; back to the review

## Lesson notes

Slide content and the full narration, in order.

Welcome to the last part of day eighteen. In part four we took a red test all the way to one line of code, and used the same loop to write tests first. Today: the browser, the test corpus, triage and release.

## Playwright smoke tests

First, the browser.

It happens more often than you think. Every thread is green, and the chat page is blank, or it answers the first message and forgets everything on the second. Why did the tests miss it? Because the threads call the agent directly, in Python. They never load the page, never send a message from it, and never keep a browser session between two requests.

**All agent tests green. Page is blank.**

> **The threads call the agent directly**
> They never load the page, send a message from it, or keep a session between requests.

The lab has a small chat page, built on the Python standard library. Run web slash app dot py and open port eight zero one eight. Each browser session gets its own agent, so state carries over between messages, just like in a thread. Every reply also returns the run ID and a turn ID, like web, then the session, then t one. So a bug found in the browser can be traced exactly like a bug found by the runner.

**The lab's chat page**

`output`
```text
http://127.0.0.1:8018  (run_id=run-...)

POST /chat  {"session_id": "...", "message": "..."}
  -> {"answer": "...", "tool": "...", "params": {...},
      "run_id": "run-...", "turn_id": "web-<session>:t1"}
```

A smoke test checks the plumbing. The page loads. A message goes in. An answer comes out. And a second message still knows about the first one. It should not re check every tool, date and number. The threads already do that, faster and more precisely. Keep it to one or two tests that run in seconds.

**What it should and should not check**

- Should: the page loads, a message goes in, an answer comes out
- Should: a second message still knows the first one
- Should not: every tool, date and number (the threads do that)
- Keep it to one or two tests that run in seconds

Here is the whole test. If Playwright is not installed, it is skipped cleanly. A fixture starts the chat server on a free port. The test opens the page, types the first question, the OAS of pool A thirty as of the twelfth, and clicks send. It waits for an answer. Then it types the follow up: and its duration as of then? It waits until there are two answers. Then it checks: the first answer has forty eight point two, and the second has five point nine one and the twelfth. That last line proves the session kept the date across two real requests.

**The whole test**

`python (shortened)`
```python
sync_api = pytest.importorskip("playwright.sync_api")

def test_two_turn_chat_carries_the_date(base_url_live):
    page.goto(base_url_live)
    page.fill("#msg", "What is the OAS of POOL-A30 as of 2026-11-12?")
    page.click("#send")
    page.wait_for_selector("[data-testid=answer]")
    page.fill("#msg", "And its duration as of then?")
    page.click("#send")
    page.wait_for_function(
        "document.querySelectorAll('[data-testid=answer]').length == 2")
    answers = page.locator("[data-testid=answer]").all_inner_texts()
    assert "48.2" in answers[0]
    assert "5.91" in answers[1] and "2026-11-12" in answers[1]
```

To run it, install pytest playwright and the chromium browser, then run pytest on the UI folder. One test, passed, in a couple of seconds. Without Playwright or a browser, it is skipped, not failed, so the rest of the suite still runs anywhere.

**One test, a few seconds**

`output`
```text
$ pip install pytest-playwright
$ python -m playwright install chromium
$ python -m pytest day18_agent_testing/tests/ui -q
.                                                    [100%]
1 passed

# without Playwright or a browser: 1 skipped, not a failure
```

Playwright or Selenium? Playwright waits for elements by default, installs its own browsers, and has a trace viewer with screenshots and video. Selenium has been around much longer, supports many languages, and many companies have huge suites in it. For a new chat app, I would pick Playwright. If your team already has a working Selenium grid, add the smoke test there. The idea matters more than the tool.

**Playwright vs Selenium**

|  | Playwright | Selenium |
|---|---|---|
| Waiting | Waits for elements by default | You add explicit waits |
| Setup | One install, bundled browsers | Drivers per browser, or a grid |
| Debugging | Trace viewer, video, screenshots | Screenshots, logs |
| Strength | New projects, fast and stable | Huge existing suites, many languages |

A flaky smoke test is worse than none, because people learn to ignore it. Four rules, all used in the lab. Select elements by a test ID, not by text or layout. Wait for a condition, like two answers on the page, never sleep for a fixed time. Use the offline agent, so the answer is the same every run. And start the server inside the test, on a free port, so nothing clashes.

**A flaky smoke test is worse than none**

1. Select by data-testid, not by text or CSS layout
2. Wait for a condition, never sleep for a fixed time
3. Use the offline agent: same answer every run
4. Start the server in the test, on a free port

## The test corpus

Now, where test cases come from. All of your tests together are your test corpus.

Five sources. Real questions from logs, with personal data removed. Domain experts, who know what analysts really ask, and how they phrase it. Every bug you have ever found, one thread per bug. Edge cases: stale data, a partial load, a pool ID that does not exist. And where you cannot use real data, licensed or synthetic data. Check the licence before any data goes into a test repo.

**Five sources**

- Real questions from logs, with personal data removed
- Domain experts: what analysts really ask
- Every bug ever found (one thread per bug)
- Edge cases: stale data, partial loads, unknown pools
- Licensed or synthetic data where you cannot use real data

Then make a coverage grid. Behaviours down one side, the thread that covers each one on the other. In the lab: pronouns are covered by bond followup. Explicit dates by explicit dates. That date after a data date question, by outlook as of and morning check. Switching dates mid thread: nothing yet, that is the lab exercise. And an unknown pool or horizon, which should give a clear tool error: nothing yet. Empty cells are your to do list.

**Empty cells are your to-do list**

| Behaviour | Thread that covers it |
|---|---|
| Pronouns: its, that one | bond_followup |
| Explicit date wins, follow-up keeps it | explicit_dates |
| "That date" after a data-date question | outlook_as_of, morning_check |
| Switching dates mid-thread | (none yet: lab step 7) |
| Unknown pool or horizon: tool error | (none yet) |

And remember, tests can be wrong too. A thread with a wrong expected date will happily pass a wrong agent, and fail a correct one. That is why step two of the debugging method checks the YAML first. And it is why new threads get a domain expert's review, which YAML makes easy.

**Review the test before the code**

> **A wrong expected date passes a wrong agent**
> Have a domain expert review new threads. In Part 4, step 2 checked the YAML first.

## Triage

Next, triage. What you do when several things are red at once.

Every failure goes into one table. One row per root cause, not per red test. Severity: a wrong number or a wrong date is high, because a person may act on it. Every row has an owner and a status. And every row links the run ID, the turn ID and the trace, so anyone can reproduce it.

**Every failure goes in one table**

- One row per root cause, not per red test
- Severity: wrong number or date = high
- Owner and status for every row
- Link the run_id, turn_id and trace

Here is today's run as a triage table. Row one: that date resolves to the partial load. Two red tests, outlook as of and morning check, both turn three. One root cause, so one row. Severity high, because the numbers were from the wrong data. Status: fixed and proven. Row two: four pytest guards fail after the fix. Severity none, expected, because they assert the bug exists. Row three: a smoke test skipped on a machine without a browser. Low, install the browser. Three rows, and nothing is lost.

**The triage table**

| Root cause | Red tests | Severity | Status |
|---|---|---|---|
| "that date" resolves to the partial load (DROP_CARRIED_AS_OF) | outlook_as_of:t3, morning_check:t3 | High | Fixed, proven |
| 4 pytest guards fail after the fix | tests/test_runner.py (4) | None | Expected |
| Smoke test skipped on one machine | tests/ui/test_smoke.py | Low | Install browser |

Quick check. Pause and answer. Five red tests this morning. Three of them show the same trace pattern, the same wrong date out of the decision step. How many triage rows? One row for the shared root cause, plus one row each for the other two, until you prove they share a cause too.

**Quick check:** Five red tests this morning. Three share the same trace pattern. How many triage rows?

<details><summary>Answer</summary>

One row for the shared root cause, plus one row for each of the other two causes (until proven the same).

</details>

## Release discipline

Finally, release discipline. Tests only help if what you ship is what you tested.

Five rules before every release. Pin the version of everything that changes behaviour: the code, the prompt, the model and the tool schemas. Run every thread, journey and smoke test on exactly that version. No open high severity rows in the triage table. Read every red or skipped test, even the expected ones. And keep the run ID with the release notes, so you can prove later what was tested.

**Ship only what you tested**

1. Pin the version: code, prompt, model and tool schemas
2. Run every thread, journey and smoke test on that version
3. No open high-severity rows in the triage table
4. Read every red or skipped test, even expected ones
5. Keep the run_id with the release notes

The classic trap: it is just a prompt change, we don't need the full suite. A prompt change is a code change. It can fix one thread and break three others, and the only way to know is to run everything. Same for a new model version, and same for a changed tool description.

**"It is just a prompt change"**

> **A prompt change is a code change**
> It can fix one thread and break three others. Run the whole suite, every time.

## Back to the review

Let's go back to where the day started. The review.

Before: twenty six of twenty eight passed. That suite is the story's, not the lab's; the lab has four threads, three threads and one journey, and seventeen pytest tests. In the story, the tests are somewhere in end to end, never replayed, and failures not traced. Now: three threads and one journey, named, in a folder you can open. The failure is outlook as of, turn three, wrong as of date. Replayed by hand, and the typed date passes. Then the trace, the root cause, the fix and the proof. That is what show me on screen looks like.

**What "show me" looks like now**

- **Before**
  - 26 of 28 passed (story suite)
  - Somewhere in end-to-end
  - Not replayed by hand
  - Failures not traced
- **Now**
  - Three threads, one journey: named
  - outlook_as_of:t3, wrong as_of
  - Replayed; typed date passes
  - Trace, root cause, fix, proof

Last quick check of the day. Your lead asks: how do you know the browser keeps the date between messages? What do you show? The smoke test. The second answer must contain five point nine one and the twelfth of November. Then run it on screen, and if needed, open that web turn in the trace.

**Quick check:** Your lead asks: "How do you know the browser keeps the date between messages?" What do you show?

<details><summary>Answer</summary>

tests/ui/test_smoke.py: the second answer must contain 5.91 and 2026-11-12. Then run it, and open the web turn_id in the trace.

</details>

Let's recap. A smoke test checks the plumbing: the page loads, a message goes in, an answer comes out, and the next message remembers. Make browser tests stable with test IDs, waits and the offline agent. Build the corpus from logs, experts, bugs and edge cases, and review the tests themselves. Triage with one row per root cause and a trace link. And release only the exact version you tested. That is day eighteen: from a pass count to proof.

- A smoke test checks plumbing: load, send, answer, remember
- Stable browser tests: test IDs, waits, offline agent
- The corpus: logs, experts, bugs, edge cases; review the tests
- Triage: one row per root cause, with a trace link
- Release only the exact version you tested

The lab, the cheat sheet and the MBS primer are linked in the description. Try lab step seven, the date switch thread, on your own. If this series helped, subscribe, and share it with someone who is learning to test AI agents.

---

← [Day 18, Part 4](day18_p4.md) · [All lessons](README.md)
