"""LLM adapters shared by the day scripts.

FakeLLM   - deterministic, no API key, used by default everywhere.
ClaudeLLM - the real thing via the Anthropic SDK (pip install anthropic, set ANTHROPIC_API_KEY).

Both expose:  complete(system, messages, tools=None) -> {"text": str, "tool_calls": [...]}
with tool_calls = [{"id": "call_1", "name": "rank_funds", "input": {...}}].

Messages use the Anthropic Messages API shape, so they pass straight through to Claude:
  {"role": "user", "content": "Which funds look best on 2025-06-19?"}
  {"role": "assistant", "content": [{"type": "text", ...}, {"type": "tool_use", "id", "name", "input"}]}
  {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_1", "content": "<json>"}]}
"""
from __future__ import annotations

import json
import re

MODEL = "claude-opus-5-5"          # set the model id once, here

TERMS = ["expense ratio", "exit load", "nav", "sip", "aum", "momentum", "elss"]
RANK_WORDS = ["top", "rank", "best", "attractive", "buy"]


def is_tool_results(msg: dict) -> bool:
    c = msg.get("content")
    return msg["role"] == "user" and isinstance(c, list) and bool(c) and \
        all(isinstance(b, dict) and b.get("type") == "tool_result" for b in c)


def final_text(messages: list[dict]) -> str:
    """The text of the last assistant message (plain string or text blocks)."""
    for m in reversed(messages):
        if m["role"] == "assistant":
            c = m["content"]
            return c if isinstance(c, str) else "".join(b.get("text", "") for b in c
                                                         if b.get("type") == "text")
    return ""


class FakeLLM:
    """A rule-based stand-in for an LLM. It picks tools by keywords, then summarises results."""

    def complete(self, system: str, messages: list[dict], tools: list[dict] | None = None) -> dict:
        last = messages[-1]
        if is_tool_results(last):                       # we have results: write the answer
            return {"text": self._summarise(last["content"]), "tool_calls": []}
        text = last["content"] if isinstance(last["content"], str) else ""
        names = {t["name"] for t in tools or []}
        if not names:
            return {"text": f"(fake LLM) You said: {text[:80]}", "tool_calls": []}
        calls = self._decide(text, names)
        if calls:
            return {"text": "", "tool_calls": [{"id": f"call_{i}", **c}
                                               for i, c in enumerate(calls, 1)]}
        return {"text": "I can rank funds, define fund terms, describe a fund or the ranking "
                        "model. Try: 'Which funds look best on 2025-06-19?'", "tool_calls": []}

    @staticmethod
    def _decide(text: str, names: set[str]) -> list[dict]:
        q = text.lower()
        calls = []
        if "rank_funds" in names and any(w in q for w in RANK_WORDS):
            args = {}
            date = re.search(r"\d{4}-\d{2}-\d{2}", text)
            year = re.search(r"\b(19|20)\d{2}\b", text)
            if date:
                args["as_of"] = date.group(0)
            elif year:
                args["as_of"] = f"{year.group(0)}-01-02"
            args["top_n"] = 3
            n = re.search(r"top\s*(\d+)", q)
            if n:
                args["top_n"] = int(n.group(1))
            if "ridge" in q:
                args["model"] = "ridge"
            calls.append({"name": "rank_funds", "input": args})
        if "model_info" in names and "model" in q and \
                any(w in q for w in ["feature", "how many", "trained", "which model"]):
            calls.append({"name": "model_info", "input": {}})
        if "lookup_definition" in names and re.search(r"what is|what does|explain|define|mean", q):
            found = [t for t in TERMS if re.search(rf"\b{t}\b", q)]
            for t in found:
                calls.append({"name": "lookup_definition", "input": {"term": t}})
            m = re.search(r"what is (?:an? |the )?([a-z][a-z ]+?)\??$", q)
            if not found and not calls and m:
                calls.append({"name": "lookup_definition", "input": {"term": m.group(1)}})
        f = re.search(r"([A-Z][a-z]+(?: [A-Z][a-z]+)* Fund)", text)
        if "fund_info" in names and f and any(w in q for w in ["tell me about", "facts", "info"]):
            calls.append({"name": "fund_info", "input": {"name": f.group(1)}})
        return calls

    @staticmethod
    def _summarise(blocks: list[dict]) -> str:
        parts = []
        for b in blocks:
            data = json.loads(b["content"])
            if "error" in data:
                parts.append(f"I could not get that: {data['error']}")
            elif "top" in data:
                names = ", ".join(f"{t['rank']}. {t['fund']} ({t['predicted_return']:+.2%})"
                                  for t in data["top"])
                parts.append(f"Top funds on {data['as_of']}: {names}. {data['caveat']}")
            elif "definition" in data:
                parts.append(f"{data['term']}: {data['definition']}")
            elif "n_features" in data:
                parts.append(f"The ranking models ({', '.join(data['models'])}) use "
                             f"{data['n_features']} features: {', '.join(data['features'])}.")
            elif "fund" in data:
                parts.append(f"{data['fund']} is a {data['category']} fund, NAV {data['nav']:.2f}, "
                             f"expense ratio {data['expense_ratio']}%.")
            else:
                parts.append(json.dumps(data))
        return " ".join(parts) + " (Synthetic data.)"


class ClaudeLLM:
    """Real Claude through the Anthropic SDK. Imported lazily so the fake path needs no key."""

    def __init__(self, model: str = MODEL, max_tokens: int = 1024):
        import anthropic
        self.client = anthropic.Anthropic()
        self.model, self.max_tokens = model, max_tokens

    def complete(self, system: str, messages: list[dict], tools: list[dict] | None = None) -> dict:
        kwargs = {"model": self.model, "max_tokens": self.max_tokens, "system": system,
                  "messages": messages}
        if tools:
            kwargs["tools"] = tools
        resp = self.client.messages.create(**kwargs)
        text = "".join(b.text for b in resp.content if b.type == "text")
        calls = [{"id": b.id, "name": b.name, "input": b.input}
                 for b in resp.content if b.type == "tool_use"]
        return {"text": text, "tool_calls": calls}


def get_llm(real: bool = False):
    return ClaudeLLM() if real else FakeLLM()
