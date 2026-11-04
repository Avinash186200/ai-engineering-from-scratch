# Day 2, Part 3: Structured Output with Pydantic: Reliable JSON from LLMs

**Watch:** [youtu.be/BntFmDMLmy0](https://youtu.be/BntFmDMLmy0) · **Code:** [`day02_prompting/`](../day02_prompting/) · **Full course playlist:** [in order](https://www.youtube.com/playlist?list=PLKRdiVI5CiMg)

Applications need fields, not paragraphs. In this episode you learn how to get JSON from a language model that your code can actually trust, and why a tool's description is itself a prompt.

## What you will learn

- Why parsing model prose with string matching breaks in production
- JSON and JSON Schema, from zero
- Constrained decoding: structured outputs and strict tool schemas
- Validating model output with Pydantic: bounds, strict mode, unions
- The retry-with-error pattern, and when to fail loudly
- How to write tool definitions the model uses correctly

## Chapters

- [0:00](https://youtu.be/BntFmDMLmy0?t=0) Intro
- [0:24](https://youtu.be/BntFmDMLmy0?t=24) Why prose breaks applications
- [0:30](https://youtu.be/BntFmDMLmy0?t=30) Why prose breaks apps
- [1:51](https://youtu.be/BntFmDMLmy0?t=111) JSON and JSON Schema, from zero
- [1:56](https://youtu.be/BntFmDMLmy0?t=116) JSON and JSON Schema
- [3:41](https://youtu.be/BntFmDMLmy0?t=221) Validating with Pydantic
- [3:49](https://youtu.be/BntFmDMLmy0?t=229) Pydantic validation
- [4:35](https://youtu.be/BntFmDMLmy0?t=275) Break it on purpose
- [6:22](https://youtu.be/BntFmDMLmy0?t=382) Retry with the error, then fail loudly
- [6:28](https://youtu.be/BntFmDMLmy0?t=388) Retry with the error
- [7:22](https://youtu.be/BntFmDMLmy0?t=442) Tool schemas are prompts too
- [7:30](https://youtu.be/BntFmDMLmy0?t=450) Tool schemas are prompts

## Lesson notes

Slide content and the full narration, in order.

Welcome back. Last time we covered prompting techniques and saved a lot of money with prompt caching. Today we make the model's output something your code can rely on.

There is some Python in this one, but I will explain every line. You can run it all from the day two folder.

## Why prose breaks applications

First, why plain sentences are a problem for software.

Priya can read, the top fund is Bharat Growth Fund, at about half a percent. A program cannot use that reliably. It needs fields: a fund name, a number, a date.

**Humans read prose. Programs need fields.**

> **"The top fund is Bharat Growth Fund, at about half a percent."**
> Fine for Priya. Useless for code that needs a fund name and a number.

The tempting shortcut is a regular expression, a text pattern that pulls the fund name out of the sentence. Do not. The model rephrases. Number formats change. A caveat mentions a second fund. It works in testing, then breaks silently in production. And a silent wrong value is worse than an error.

**Never parse model prose with regex**

- The model rephrases: "leading the pack is..."
- Number formats change: 0.53% vs 0.0053 vs +0.5300%
- A caveat mentions a second fund name
- Worked in testing, breaks silently in production

*A silent wrong value is worse than an error.*

Structured output means the model returns data in a machine readable format, almost always JSON, matching a shape you defined. There are three layers. First, constrain the generation: tell the model the exact shape you need.

Second, validate the result in your own code, never trusting layer one alone. Third, if it fails, send the error back once so the model can fix it, and if it still fails, raise a loud error. Let's take them one by one.

**Three layers, used together**

1. Constrain: ask for JSON matching a schema
2. Validate: check it in your own code with Pydantic
3. Retry once with the error, then fail loudly

## JSON and JSON Schema, from zero

First, the vocabulary: JSON and JSON Schema.

JSON is just a text format for data. Curly braces hold an object with named fields. Square brackets hold a list. Strings sit in quotes, and numbers do not. This is what our rank funds tool returns: a date, how many funds were scored, the top list, and a caveat.

**A text format for data**

`rank_funds("2025-06-19", top_n=1) returns`
```python
{
  "as_of": "2025-06-19",
  "n_scored": 120,
  "top": [
    {"rank": 1, "fund": "Bharat Growth Fund",
     "predicted_return": 0.0053, "nav": 48.72}
  ],
  "caveat": "Research signal from a backtested model."
}
```

JSON Schema describes what valid JSON must look like. Think of it as the printed form at a bank, with labelled boxes. Type says what kind of value. Properties and required list the fields. Minimum and maximum set bounds. Enum means pick from a fixed list. And additional properties false means no extra boxes allowed.

**The rules for what valid JSON looks like**

| Keyword | Meaning |
|---|---|
| type | object, array, string, number, integer... |
| properties / required | Which fields exist; which must be present |
| minimum / maximum | Numeric bounds |
| enum | Value must be one of a fixed list |
| additionalProperties: false | No unknown fields allowed |

How do providers enforce a schema? At every step, as the model picks its next token, any token that would break the schema is blocked. Only valid continuations can be chosen. This is called constrained decoding. But notice: it guarantees the shape, never the truth.

**How providers guarantee the shape**

> **At each step, tokens that would break the schema are blocked.**
> Called structured outputs, or strict tool schemas. Guarantees shape, never truth.

Here is the ladder. Asking for JSON in the prompt guarantees nothing. JSON mode guarantees the brackets are right, but not your fields. Structured outputs and strict tool schemas match your schema exactly. But none of them guarantee correct values. A perfectly shaped reply can still name the wrong fund.

**From asking nicely to strict schemas**

| Approach | Guarantees | Does not |
|---|---|---|
| Ask for JSON in prompt | Nothing | May add prose, miss fields |
| JSON mode | Valid JSON syntax | Your fields and types |
| Structured outputs | Matches your schema | Correct values |
| Strict tool schemas | Tool arguments match | Correct values |

*A valid-looking reply can still name the wrong fund.*

## Validating with Pydantic

That is why layer two exists: validation in your own code, with Pydantic.

Pydantic is the standard Python library for this. You declare the shape as a class with type hints. Field adds rules beyond the type: rank at least one, predicted return between minus one and one, net asset value above zero. And a business rule: at most fifty rows, and the caveat must never be empty.

**Declare the shape once, as a class**

`day02_prompting/structured_output.py`
```python
from pydantic import BaseModel, ConfigDict, Field

class Row(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    rank: int = Field(ge=1)
    fund: str
    predicted_return: float = Field(ge=-1, le=1)   # a decimal, 0.0053
    nav: float = Field(gt=0)

class Ranking(BaseModel):
    as_of: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    n_scored: int = Field(ge=0)
    top: list[Row] = Field(min_length=1, max_length=50)
    caveat: str = Field(min_length=1)    # never drop the caveat
```

One class does three jobs. It generates the JSON schema you send to the model. It validates the reply. And it documents the shape for your teammates. Run it yourself: python day two prompting, structured output dot p y.

**One class, three jobs**

- Ranking.model_json_schema() -> the schema you send the model
- Ranking.model_validate(data) -> the check you run on the reply
- Plus readable documentation of the shape

The best way to learn validation is to break it on purpose. Set the predicted return to fifty three point zero eight, a percentage written where a decimal belongs. Pydantic says: input should be less than or equal to one. That is the classic units bug, caught by a simple bound.

Now set the net asset value to the text, forty eight point seven two, in quotes. By default, Pydantic quietly converts it to a number and passes. That is called coercion. With strict mode on, it becomes an error, which is usually what you want when checking a model's output.

Ask for a Sunday, and the tool returns an error object instead of a ranking. So accept either shape, a ranking or a tool error, and branch on which one you got. And the big lesson: ask for five hundred funds, and every row is individually valid, so it passes. Only the fifty row business rule catches it. Schemas check shape. Business rules check meaning.

**What validation catches**

| Break | Result |
|---|---|
| predicted_return = 53.08 (percent, not decimal) | Error: should be <= 1 |
| nav = "48.72" (a string) | Passes by default! Error only with strict=True |
| rank_funds("2025-06-15") (a Sunday) | Returns {"error": ...}: accept Ranking \| ToolError |
| rank_funds(top_n=500): every row valid | Passes! Only max_length=50 catches it |

*Schemas check shape. Business rules check meaning.*

If you have done some machine learning, this is a data contract: column present, type correct, value in range, no surprise columns. You already put that check at the start of a feature pipeline. Validating model output is the same check, moved to the other end. And yes, the percent versus decimal bug is one you have probably met in a backtest.

**A data contract at the end of the pipe**

> **Column present, type correct, value in range, no surprise columns.**
> The same check you put at the start of a feature pipeline, moved to the model's output.

## Retry with the error, then fail loudly

Now layer three: what to do when validation fails.

The best repair is to show the model its exact error. Pydantic errors are precise, like, top, zero, predicted return, should be at most one. Models fix those well. First json loads checks the syntax, then Pydantic checks the shape and the rules. If it fails, we append the error and ask again.

**Show the model its exact mistake**

`day02_prompting/structured_output.py`
```python
def ask_for_json(llm, system, messages, schema_cls, max_retries=1):
    msgs = list(messages)
    for attempt in range(max_retries + 1):
        reply = llm.complete(system, msgs)["text"]
        try:
            return schema_cls.model_validate(json.loads(reply))
        except (json.JSONDecodeError, ValidationError) as exc:
            if attempt == max_retries:
                raise StructuredOutputError(f"invalid after retry: {exc}")
            fix = f"Your JSON failed validation:\n{exc}\nReturn corrected JSON only."
            msgs += [{"role": "assistant", "content": reply},
                     {"role": "user", "content": fix}]
```

Two traps. Retrying without the error message, so the model repeats the mistake. And retrying without a limit, so one strange input costs unlimited money. Retry once, then fail loudly and tell the user you could not produce a valid result. And track your retry rate. When it climbs, something broke.

**Two retry traps**

- Retrying without the error: the same mistake again
- Retrying without a limit: one bad input, unlimited cost
- Final failure: "I could not produce a valid result", never half-parsed

*Count retries: a rising retry rate is an early warning.*

## Tool schemas are prompts too

One last idea. The model reads your tool definitions too, so they are prompts.

The model decides which tool to call, and with what arguments, by reading the tool's name and description. Compare: tool two, runs the model. The model has to guess. Versus rank funds: what it does, when to use it in the words analysts actually use, and the valid date range.

**A weak vs a good tool description**

- **Weak**
  - name: tool2
  - "Runs the model."
  - The model has to guess
- **Good**
  - name: rank_funds
  - What: ranks funds by predicted return
  - When: "best", "top", "attractive"
  - Limits: dates 2020-01-01 to 2025-06-19

Here is a tightened schema. A date pattern with an example format. An enum for category, so the model cannot invent a fourth type. A minimum and maximum on top n, so a request for five hundred is rejected before the tool even runs. And no extra fields allowed.

**A strict schema for rank_funds**

`rank_funds input_schema`
```python
{
  "type": "object",
  "properties": {
    "as_of": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
              "description": "Business day, YYYY-MM-DD. Omit for latest."},
    "category": {"type": "string", "enum": ["equity", "debt", "hybrid"]},
    "top_n": {"type": "integer", "minimum": 1, "maximum": 50,
              "description": "How many funds to return, e.g. 10."}
  },
  "additionalProperties": false
}
```

Two more habits. The tool's error message is read by the model and shapes what it says next, so make it helpful: no data for this date, maybe a Sunday, try a nearby weekday. And always validate arguments again in your own code. The schema checks shape; your code knows the business rules.

**Errors and double-checks**

- Error text is read by the model: make it helpful
- "No data for 2025-06-15 (a Sunday?). Try a nearby weekday."
- Validate arguments again in your code before running the tool

Quick check. Strict schema is on, and Pydantic validation passes. Can the answer still name the wrong top fund? Pause and think. The answer is yes. Schemas guarantee shape, never truth. We need checks against the tool's output, which we cover in the next part.

**Quick check:** Strict schema on, Pydantic passes. Can the answer still name the wrong top fund?

<details><summary>Answer</summary>

Yes. Schemas guarantee shape, never truth. Numbers and names must be checked against the tool.

</details>

Let's recap. Never parse model prose with a regex. Use three layers: constrain, validate, then retry once and fail loudly. Pydantic gives you bounds, strict mode, unions and business rules. Schemas check shape; business rules check meaning. And tool descriptions are prompts that steer the model. Next: prompt injection, guardrails, and how to test a prompt change.

- Never parse model prose with regex
- Three layers: constrain, validate, retry then fail loudly
- Pydantic: bounds, strict mode, unions, business rules
- Schemas check shape; business rules check meaning
- Tool names, descriptions and bounds steer the model

Structured output dot p y is in the day two folder, linked in the description. Break it on purpose yourself. Subscribe, and see you in the next part.

---

← [Day 2, Part 2](day02_p2.md) · [All lessons](README.md) · [Day 2, Part 4](day02_p4.md) →
