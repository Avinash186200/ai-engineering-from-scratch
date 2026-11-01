"""Structured output: ask for JSON, validate it with Pydantic, retry with the error if it fails.

Run:  python day02_prompting/structured_output.py          (FakeLLM, no key)
      python day02_prompting/structured_output.py --real   (Claude, needs ANTHROPIC_API_KEY)
"""
import argparse
import json
import sys
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.llm import get_llm  # noqa: E402

SYSTEM = (Path(__file__).with_name("system_prompt.md")).read_text(encoding="utf-8")


class FundPick(BaseModel):
    fund: str
    category: str
    reason: str = Field(max_length=200)
    confidence: float = Field(ge=0, le=1)


class ScriptedFakeLLM:
    """First answer is broken on purpose (confidence 1.4, wrapped in prose); second is valid."""

    def __init__(self):
        self.calls = 0

    def complete(self, system, messages, tools=None):
        self.calls += 1
        if self.calls == 1:
            return {"text": 'Sure! {"fund": "Bharat Growth Fund", "category": "equity_large", '
                            '"reason": "Strong 3 month momentum", "confidence": 1.4}', "tool_calls": []}
        return {"text": '{"fund": "Bharat Growth Fund", "category": "equity_large", '
                        '"reason": "Strong 3 month momentum and a low expense ratio", "confidence": 0.7}',
                "tool_calls": []}


def extract_json(text: str) -> str:
    start, end = text.find("{"), text.rfind("}")
    return text[start:end + 1] if start >= 0 else text


def ask_for_pick(llm, question: str, max_tries: int = 3) -> FundPick:
    messages = [{"role": "user", "content": question}]
    for attempt in range(1, max_tries + 1):
        raw = llm.complete(SYSTEM, messages)["text"]
        print(f"attempt {attempt}: {raw}")
        try:
            return FundPick.model_validate(json.loads(extract_json(raw)))
        except (json.JSONDecodeError, ValidationError) as e:
            err = str(e).splitlines()[0:3]
            print(f"  invalid -> {' | '.join(err)}")
            messages += [{"role": "assistant", "content": raw},
                         {"role": "user", "content": f"Your JSON was invalid: {err}. Reply with JSON only."}]
    raise RuntimeError("model never produced valid JSON")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true")
    args = ap.parse_args()
    llm = get_llm(True) if args.real else ScriptedFakeLLM()
    pick = ask_for_pick(llm, "Pick one large-cap fund from: Bharat Growth Fund, Nifty Value Fund.")
    print("validated:", pick.model_dump())
