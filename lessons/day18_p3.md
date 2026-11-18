# Day 18, Part 3: Testing AI Agents: YAML Tests, Run IDs and Spans

**Watch:** video coming soon · **Code:** [`day18_agent_testing/`](../day18_agent_testing/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

A test file a domain expert can read, and a trace that shows every decision the agent made. This episode covers writing agent tests as YAML data, the four checks the runner makes on every turn, and tracing: traces, spans and generations, run IDs and turn IDs, and how hosted tools and dashboards fit in.

## What you will learn

- Why agent tests work best as data, not code
- The fields of a thread: expect_tool, expect_params, expect_as_of, grounded_keys
- Subset matching, and the grounding check that catches invented numbers
- Trace, span and generation, mapped to one real turn
- run_id and turn_id, the local JSONL trace, Langfuse and dashboards

## Lesson notes

Slide content and the full narration, in order.

Welcome back. In part two we found the threads, replayed them by hand, and saw why four steps out of five is still a fail. Today, two tools that make all of that easier: writing tests as YAML, and tracing every turn.

## Tests as data

First, why the tests are YAML files, and not Python code.

You could write every thread as a Python test. But then the conversation, the expected calls and the checking logic are all mixed together, and only engineers can review it. Write the tests as data instead. One runner, many YAML files, every test the same shape. Now a fixed income expert can read a thread and say: no, as of then should mean the twelfth, not the thirteenth. That review is worth a lot.

**Tests in code vs tests as data**

- **In code**
  - Logic and data mixed
  - Only engineers can review
  - Each test a bit different
- **As YAML data**
  - One runner, many files
  - A domain expert can review
  - Every test has the same shape

Each turn has five fields. User is the message. Expect tool is the tool the agent should call first, or null for no tool. Expect params lists only the parameters you care about. Expect as of is the date argument, checked on its own, because dates are where the worst bugs live. And grounded keys names values from the tool output that must appear in the answer.

**Five fields per turn**

| Field | What it checks |
|---|---|
| user | The message sent to the agent |
| expect_tool | The name of the first tool called, or null for no tool |
| expect_params | Only the keys you list (a subset match) |
| expect_as_of | The as_of argument of the call, or null |
| grounded_keys | These tool output values must appear in the answer |

Here is the checking code, check turn, in the runner. Four checks. The tool name. Each listed parameter, as a subset match. The as of date. And grounding: each named value from the tool output must appear in the answer text. Every failure adds a plain English reason. That is where the line, as of expected the thirteenth got the fourteenth, comes from.

**The runner makes four checks**

`python (shortened)`
```python
if actual_tool != spec.get("expect_tool"):
    reasons.append(f"tool: expected ... got ...")
for k, v in (spec.get("expect_params") or {}).items():   # subset match
    if params.get(k) != v:
        reasons.append(f"param {k}: expected ... got ...")
if "expect_as_of" in spec and params.get("as_of") != spec["expect_as_of"]:
    reasons.append(f"as_of: expected ... got ...")
for key in spec.get("grounded_keys") or []:
    if str(out[key]) not in result.answer:
        reasons.append(f"grounded: answer missing {key}=...")
```

Why a subset match? Because a test that pins every key breaks on harmless changes. If someone adds an optional parameter to the tool, an exact match fails every thread, and people start ignoring red builds. So list only what matters for this turn. Here, the horizon. The date has its own field.

**List only what matters**

> **expect_params: {horizon_days: 5}**
> Extra keys in the call are fine. A test that pins every key breaks on harmless changes.

Now grounding, with a real test from the lab. The tool returned a rate change of minus two point four. If the answer says minus two point four, the check passes. If the answer says minus nine point nine, the check fails, even though the right tool was called with the right date. This catches the model that calls the tool, then writes a different number anyway.

**Grounding: no invented numbers**

`python`
```python
spec = {"expect_tool": "get_outlook", "grounded_keys": ["rate_change_bp"]}
call = {"name": "get_outlook", "params": {},
        "output": {"rate_change_bp": -2.4}}

check_ok(spec, TurnResult("rates -2.4 bp", [call]))   # True
check_ok(spec, TurnResult("rates -9.9 bp", [call]))   # False
```

A worked example: the explicit dates thread. It tests three rules in four turns. Turn one gives a date, the twelfth, so the explicit date wins. Turn two, now the five day, keeps the twelfth. Turn three asks for the latest snapshot date. Turn four, the five day outlook again, now uses the thirteenth, because asking for the data date re anchors the conversation. Is that the right rule? That is exactly the question a domain expert can answer by reading the YAML.

**Three rules in four turns**

`yaml (shortened)`
```yaml
- user: "What's the 21-day outlook as of 2026-11-12?"
  expect_params: {horizon_days: 21}
  expect_as_of: "2026-11-12"          # explicit date wins
- user: "Now the 5-day"
  expect_params: {horizon_days: 5}
  expect_as_of: "2026-11-12"          # follow-up keeps it
- user: "What date is the latest snapshot?"
  expect_tool: get_snapshot_date
  expect_as_of: null
- user: "The 5-day outlook again, please"
  expect_as_of: "2026-11-13"          # data-date question re-anchors
```

Five habits for writing a good thread. Start with one comment saying what it protects. Expect the call, not the exact wording of the answer. Always set expect as of when a date is involved. Ground the numbers a person will act on. And watch the test fail once before you trust it. A test that has never failed might not be testing anything.

**Tests that stay useful**

1. One comment at the top: what this thread protects
2. Expect the call, not the exact wording
3. Always set expect_as_of when a date is involved
4. Ground the numbers the user will act on
5. Watch it fail once before you trust it

Quick check. Pause and answer. Turn three calls the right tool with the right date, but the answer says minus nine point nine, while the tool returned minus two point four. Which check fails? The grounding check. The answer is missing the rate change value the tool returned.

**Quick check:** Turn 3 calls the right tool with the right date, but the answer says -9.9 bp while the tool returned -2.4. Which check fails?

<details><summary>Answer</summary>

grounded_keys: the answer is missing rate_change_bp=-2.4.

</details>

## Tracing

Tests tell you that a turn failed. Traces tell you why. Now, tracing.

Three words, used by most tracing tools. A trace is everything that happened for one turn. A generation is one call to the language model. A span is any other step, like a tool call. In the lab, each turn is a trace called agent turn. The decide tool generation picks the tool and its arguments. The tool span runs it. The compose answer generation writes the reply. And every record carries two IDs: the run ID and the turn ID.

**Trace, span, generation**

| Word | Meaning | In the lab |
|---|---|---|
| Trace | Everything for one turn | agent_turn |
| Generation | One model (LLM) call | decide_tool, compose_answer |
| Span | One other step, like a tool call | tool:get_outlook |
| run_id / turn_id | Which run, which turn | run-...-c6b6, outlook_as_of:t3 |

In order: the trace input records state in, what the agent knew before the turn. Then the decision: which tool, which arguments. Then the tool span, with its exact inputs and outputs. Then the answer, and state out, what the agent knows after. This order is what makes debugging fast. If state in is right and the call is wrong, the bug is in the decision step. If the call is right and the output is wrong, look at the tool.

**What a trace records**

**state_in** (what the agent knew) → **decide_tool** (which tool, which args) → **tool span** (inputs and outputs) → **state_out** (what it knows now)

*If state_in is right and the call is wrong, look at the decision step.*

The tracer is small. A run ID is the word run, the date and time, and four random characters. Every record is one line of JSON in traces slash run ID dot JSONL, with a type, a turn ID, like bond followup colon t one, and the run ID. The turn ID is the thread name plus the turn number. With those two IDs, you can jump from a red line in the report to the exact record in seconds.

**Every record has a run_id and a turn_id**

`python (shortened)`
```python
def new_run_id():
    return time.strftime("run-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]

# one line per record in traces/<run_id>.jsonl
{"type": "trace", "turn_id": "bond_followup:t1", "name": "agent_turn",
 "input": {"user": "...", "state_in": {...}}, "run_id": "run-20261118-231305-c6b6"}
```

Show trace has three modes. With no arguments, it lists the runs it has. With a run ID, it prints every turn. And with dash dash turn, it prints just one. Let's open a passing turn first, bond followup turn one, so we know what normal looks like.

**List runs, then open one turn**

`output`
```text
$ python day18_agent_testing/tools/show_trace.py
run-20261118-231305-c6b6

$ python day18_agent_testing/tools/show_trace.py \
      run-20261118-231305-c6b6 --turn bond_followup:t1
```

Here it is. The input: the user asked for the OAS of pool A thirty as of the twelfth, and state in is empty, because this is the first turn. The decide tool generation chose get bond metrics, pool A thirty, the twelfth. The tool span returned an OAS of forty eight point two basis points, duration five point nine one, convexity minus one point one two. The answer quotes forty eight point two. And state out now holds the twelfth and pool A thirty. Every step agrees. That is what healthy looks like.

**A healthy turn**

`output`
*(output trimmed)*

```text
TRACE 082b8bcb593a  turn_id=bond_followup:t1
  input: {"user": "What is the OAS of POOL-A30 as of 2026-11-12?",
          "state_in": {"as_of": null, "latest_available": null, ...}}
  ├─ GENERATION decide_tool (model=scripted-rules)
  │    output: {"tool": "get_bond_metrics",
  │             "params": {"bond_id": "POOL-A30", "as_of": "2026-11-12"}}
  ├─ SPAN tool:get_bond_metrics
  │    output: {"oas_bp": 48.2, "eff_duration": 5.91, "convexity": -1.12, ...}
  ├─ GENERATION compose_answer (model=scripted-rules)
  └─ OUTPUT {"answer": "POOL-A30 as of 2026-11-12: OAS 48.2 bp, ...",
             "state_out": {"as_of": "2026-11-12", "last_bond": "POOL-A30", ...}}
```

Why does this matter? Because two bugs that look the same in the answer have different fixes. If the arguments are right and the tool returns bad data, look at the tool or the data. If state in had the right date and the decision step picked the wrong one, look at the decision step. Without a trace, you would guess, and most people guess the prompt.

**The trace tells them apart**

- **Right call, wrong output**
  - decide_tool args are correct
  - Tool span returns bad data
  - Look at the tool or the data
- **Wrong call**
  - state_in has the right date
  - decide_tool picks the wrong one
  - Look at the decision step

## Hosted tools and dashboards

The lab writes local files. In production, you usually add a hosted tracing tool and dashboards.

The lab's tracer can also send records to Langfuse, an open source LLM tracing tool. Install the package, set the public and secret keys, and each trace, span and generation is sent there too. You get a web UI, search by run ID or turn ID, and cost and latency per call. If Langfuse is not set up, nothing breaks. The local JSONL file is always written.

**The same records, in a web UI**

- pip install langfuse; set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY
- The tracer also sends each trace, span and generation
- Search by run_id or turn_id; see cost and latency
- The local JSONL file is always written as well

Then build dashboards, for example in Grafana, from those records. Count the failures that matter for your domain. For this agent: how many tool calls per day used a date different from the one the user anchored to. How many answers came from a partial load. Tool errors per tool. And latency and cost per turn. A spike in the first chart is this bug, found in production before a user reports it.

**Count the failures that matter**

- as_of mismatches per day: tool date vs anchored date
- Answers from a partial load
- Tool errors and empty results per tool
- Latency and cost per turn

Before you switch tracing on in production, think about privacy and cost. Traces hold user messages, so mask personal data. Decide how long traces are kept. Sample in production if volume is high, but trace every test run. And never write keys or secrets into a trace.

**Privacy and cost**

- Traces hold user messages: mask personal data
- Set how long traces are kept
- Sample in production; trace every test run
- Never put keys or secrets in a trace

Quick check. Pause and answer. A trace shows state in, as of the thirteenth. But the decide tool generation outputs as of the fourteenth. Where is the bug? In the decision step. The right date was in state and was not used. Not in the tool, and not in the data. Hold on to that. It is exactly what we will see in part four.

**Quick check:** A trace shows state_in.as_of = 2026-11-13, but decide_tool outputs as_of = 2026-11-14. Where is the bug?

<details><summary>Answer</summary>

In the decision step: the right date was in state and was not used. Not the tool, not the data.

</details>

Let's recap. Write tests as YAML: one runner, and files a domain expert can read. The runner makes four checks on every turn: tool, parameters as a subset, as of, and grounding. A trace is one turn, a generation is a model call, and a span is a tool call. The run ID and turn ID take you from a red line to the exact record. And hosted tools and dashboards are built on the same records. Next: we debug the planted bug, live, and then use test driven development.

- Tests as YAML: one runner, files a domain expert can read
- Four checks per turn: tool, params (subset), as_of, grounding
- Trace = one turn; generation = model call; span = tool call
- run_id + turn_id take you from a red line to the record
- Hosted tools and dashboards use the same records

The runner, the tracer and the trace viewer are linked in the description. Open one passing turn and one failing turn yourself before the next part. If this helped, subscribe, and I will see you in the next video.

---

← [Day 18, Part 2](day18_p2.md) · [All lessons](README.md) · [Day 18, Part 4](day18_p4.md) →
