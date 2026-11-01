"""LLM adapters shared by the day scripts.

FakeLLM  - deterministic, no API key, used by default everywhere.
ClaudeLLM - the real thing via the Anthropic SDK (pip install anthropic, set ANTHROPIC_API_KEY).

Both expose:  complete(system, messages, tools=None) -> {"text": str, "tool_calls": [...]}
Messages use a simple neutral format:
  {"role": "user", "content": "..."}
  {"role": "assistant", "content": "...", "tool_calls": [{"id", "name", "args"}]}
  {"role": "tool", "tool_call_id": "...", "name": "...", "content": "<json string>"}
"""
from __future__ import annotations

import json
import re

MODEL = "claude-opus-5-5"


class FakeLLM:
    """A rule-based stand-in for an LLM. It picks tools by keywords, then summarises results."""

    def complete(self, system: str, messages: list[dict], tools: list[dict] | None = None) -> dict:
        last = messages[-1]
        if last["role"] == "tool":                      # we have results: write the answer
            return {"text": self._summarise(messages), "tool_calls": []}
        text = last["content"]
        q = text.lower()
        if not tools:
            return {"text": self._plain(text), "tool_calls": []}
        calls = []
        if any(w in q for w in ["top", "rank", "best"]):
            date = re.search(r"\d{4}-\d{2}-\d{2}", text)
            n = re.search(r"top\s*(\d+)", q)
            args = {"top_n": int(n.group(1)) if n else 5}
            if date:
                args["as_of"] = date.group(0)
            calls.append({"id": "call_1", "name": "rank_funds", "args": args})
        m = re.search(r"(?:what is|define|meaning of)\s+(?:an?\s+|the\s+)?([a-z ]+?)[?.]?$", q)
        if m:
            calls.append({"id": f"call_{len(calls)+1}", "name": "lookup_term",
                          "args": {"term": m.group(1).strip()}})
        f = re.search(r"([A-Z][a-z]+(?: [A-Z][a-z]+)* Fund)", text)
        if f and ("tell me about" in q or "info" in q):
            calls.append({"id": f"call_{len(calls)+1}", "name": "fund_info", "args": {"name": f.group(1)}})
        if calls:
            return {"text": "", "tool_calls": calls}
        return {"text": "I can rank funds, define terms, or describe a fund. "
                        "Try: 'top 3 funds on 2024-11-04'.", "tool_calls": []}

    def _plain(self, text: str) -> str:
        return f"(fake LLM) You said: {text[:80]}"

    def _summarise(self, messages: list[dict]) -> str:
        parts = []
        for m in reversed(messages):
            if m["role"] != "tool":
                break
            data = json.loads(m["content"])
            if "error" in data:
                parts.append(f"The tool reported a problem: {data['error']}")
            elif "top" in data:
                names = ", ".join(f"{t['rank']}. {t['fund']} ({t['predicted_return']:+.2%})" for t in data["top"])
                parts.append(f"Top funds on {data['as_of']}: {names}.")
            elif "definition" in data:
                parts.append(f"{data['term'].upper()}: {data['definition']}")
            elif "fund" in data:
                parts.append(f"{data['fund']} is a {data['category']} fund, NAV {data['nav']:.2f}, "
                             f"expense ratio {data['expense_ratio']}%.")
        return " ".join(reversed(parts)) + " (Synthetic data, not investment advice.)"


class ClaudeLLM:
    """Real Claude through the Anthropic SDK. Imported lazily so the fake path needs no key."""

    def __init__(self, model: str = MODEL, max_tokens: int = 1024):
        import anthropic
        self.client = anthropic.Anthropic()
        self.model, self.max_tokens = model, max_tokens

    @staticmethod
    def _to_anthropic(messages: list[dict]) -> list[dict]:
        out = []
        for m in messages:
            if m["role"] == "user":
                out.append({"role": "user", "content": m["content"]})
            elif m["role"] == "assistant":
                blocks = [{"type": "text", "text": m["content"]}] if m.get("content") else []
                blocks += [{"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["args"]}
                           for c in m.get("tool_calls", [])]
                out.append({"role": "assistant", "content": blocks})
            elif m["role"] == "tool":
                block = {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}
                if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                    out[-1]["content"].append(block)
                else:
                    out.append({"role": "user", "content": [block]})
        return out

    def complete(self, system: str, messages: list[dict], tools: list[dict] | None = None) -> dict:
        kwargs = {"model": self.model, "max_tokens": self.max_tokens, "system": system,
                  "messages": self._to_anthropic(messages)}
        if tools:
            kwargs["tools"] = tools
        resp = self.client.messages.create(**kwargs)
        text = "".join(b.text for b in resp.content if b.type == "text")
        calls = [{"id": b.id, "name": b.name, "args": b.input} for b in resp.content if b.type == "tool_use"]
        return {"text": text, "tool_calls": calls}


def get_llm(real: bool = False):
    return ClaudeLLM() if real else FakeLLM()
