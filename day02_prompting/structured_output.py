"""Structured output: declare the shape with Pydantic, validate, and retry once with the error.

Run:  python day02_prompting/structured_output.py          (scripted fake, no key)
      python day02_prompting/structured_output.py --real   (Claude, needs ANTHROPIC_API_KEY)
"""
import argparse
import json
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.fund_model import rank_funds  # noqa: E402
from core.llm import get_llm  # noqa: E402


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


class ToolError(BaseModel):
    error: str


class StructuredOutputError(Exception):
    pass


def ask_for_json(llm, system, messages, schema_cls, max_retries=1):
    msgs = list(messages)
    for attempt in range(max_retries + 1):
        reply = llm.complete(system, msgs)["text"]
        print(f"  attempt {attempt + 1}: {reply[:110]}")
        try:
            return schema_cls.model_validate(json.loads(reply))
        except (json.JSONDecodeError, ValidationError) as exc:
            if attempt == max_retries:
                raise StructuredOutputError(f"invalid after retry: {exc}")
            fix = f"Your JSON failed validation:\n{exc}\nReturn corrected JSON only."
            msgs += [{"role": "assistant", "content": reply},
                     {"role": "user", "content": fix}]


def parse_tool_result(result: dict) -> Ranking | ToolError:
    """Accept either shape, a ranking or a tool error, and branch on which one you got."""
    return ToolError(**result) if "error" in result else Ranking.model_validate(result)


class ScriptedFakeLLM:
    """First reply uses a percent instead of a decimal (53.08); after the error it is fixed."""

    def __init__(self, good: dict):
        self.good, self.calls = good, 0

    def complete(self, system, messages, tools=None):
        self.calls += 1
        bad = json.loads(json.dumps(self.good))
        bad["top"][0]["predicted_return"] = 53.08
        return {"text": json.dumps(bad if self.calls == 1 else self.good), "tool_calls": []}


SYSTEM = ("Reply with JSON only, matching: {as_of, n_scored, top: [{rank, fund, "
          "predicted_return (decimal), nav}], caveat}.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true")
    args = ap.parse_args()
    truth = {k: v for k, v in rank_funds("2025-06-19", top_n=1).items()
             if k in ("as_of", "n_scored", "top", "caveat")}
    print('rank_funds("2025-06-19", top_n=1) ->', json.dumps(truth))
    llm = get_llm(True) if args.real else ScriptedFakeLLM(truth)
    question = f"Restate this ranking as JSON: {json.dumps(truth)}"
    print("ask_for_json:")
    ranking = ask_for_json(llm, SYSTEM, [{"role": "user", "content": question}], Ranking)
    print("  validated:", ranking.model_dump())

    print("\nBreak it on purpose:")
    row = dict(truth["top"][0])
    for label, data, cls in [
        ("predicted_return = 53.08", {**row, "predicted_return": 53.08}, Row),
        ('nav = "48.72" (a string)', {**row, "nav": "48.72"}, Row),
        ("500 rows", {**truth, "top": [row] * 500}, Ranking),
        ("caveat dropped", {**truth, "caveat": ""}, Ranking),
    ]:
        try:
            cls.model_validate(data)
            print(f"  {label:<26} passes")
        except ValidationError as exc:
            print(f"  {label:<26} rejected: {exc.errors()[0]['msg']}")
    sunday = parse_tool_result(rank_funds("2025-06-15"))
    print(f"  {'rank_funds(2025-06-15)':<26} {type(sunday).__name__}: {sunday.error}")
