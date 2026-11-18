"""Tracing: always writes local JSONL (traces/<run_id>.jsonl).

Records are shaped like Langfuse objects: trace -> span (tool) / generation (LLM).
If the `langfuse` package is installed AND LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY
are set, records are also sent to Langfuse (best effort; failures are ignored).
"""
import json
import os
import time
import uuid
from pathlib import Path

TRACE_DIR = Path(__file__).resolve().parent.parent / "traces"


def _langfuse_client():
    if not (os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")):
        return None
    try:
        from langfuse import Langfuse  # optional
        return Langfuse()
    except Exception:
        return None


class Tracer:
    def __init__(self, run_id, trace_dir=TRACE_DIR):
        self.run_id = run_id
        trace_dir = Path(trace_dir)
        trace_dir.mkdir(parents=True, exist_ok=True)
        self.path = trace_dir / f"{run_id}.jsonl"
        self.lf = _langfuse_client()

    def _write(self, rec):
        rec.setdefault("ts", time.time())
        rec["run_id"] = self.run_id
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        if self.lf is not None:
            self._send_langfuse(rec)
        return rec["id"]

    def _send_langfuse(self, rec):
        try:  # Langfuse SDK v2-style API; ignore if the installed version differs
            if rec["type"] == "trace":
                self.lf.trace(id=rec["id"], name=rec["name"], input=rec.get("input"),
                              metadata={"run_id": self.run_id, "turn_id": rec["turn_id"]})
            elif rec["type"] == "span":
                self.lf.span(trace_id=rec["trace_id"], name=rec["name"],
                             input=rec.get("input"), output=rec.get("output"))
            elif rec["type"] == "generation":
                self.lf.generation(trace_id=rec["trace_id"], name=rec["name"], model=rec.get("model"),
                                   input=rec.get("input"), output=rec.get("output"))
            self.lf.flush()
        except Exception:
            pass

    def trace(self, turn_id, name, input, metadata=None):
        tid = uuid.uuid4().hex[:12]
        self._write({"type": "trace", "id": tid, "trace_id": tid, "parent_id": None,
                     "turn_id": turn_id, "name": name, "input": input, "metadata": metadata or {}})
        return tid

    def span(self, trace_id, turn_id, name, input, output, error=None):
        return self._write({"type": "span", "id": uuid.uuid4().hex[:12], "trace_id": trace_id,
                            "parent_id": trace_id, "turn_id": turn_id, "name": name,
                            "input": input, "output": output, "error": error})

    def generation(self, trace_id, turn_id, name, model, input, output):
        return self._write({"type": "generation", "id": uuid.uuid4().hex[:12], "trace_id": trace_id,
                            "parent_id": trace_id, "turn_id": turn_id, "name": name, "model": model,
                            "input": input, "output": output})

    def end_trace(self, trace_id, turn_id, output):
        return self._write({"type": "trace_end", "id": uuid.uuid4().hex[:12], "trace_id": trace_id,
                            "parent_id": trace_id, "turn_id": turn_id, "name": "turn_output",
                            "output": output})


def new_run_id():
    return time.strftime("run-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
