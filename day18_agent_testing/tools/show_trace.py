"""Print a trace tree from traces/<run_id>.jsonl.

    python day18_agent_testing/tools/show_trace.py                      # list runs
    python day18_agent_testing/tools/show_trace.py <run_id>             # every turn
    python day18_agent_testing/tools/show_trace.py <run_id> --turn outlook_as_of:t3
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TRACE_DIR = Path(__file__).resolve().parent.parent / "traces"


def load(run_id, trace_dir=TRACE_DIR):
    path = Path(trace_dir) / f"{run_id}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def render(records, turn=None):
    lines = []
    for rec in records:
        if turn and rec["turn_id"] != turn:
            continue
        if rec["type"] == "trace":
            lines.append(f"TRACE {rec['id']}  turn_id={rec['turn_id']}")
            lines.append(f"  input: {json.dumps(rec['input'])}")
        elif rec["type"] == "generation":
            lines.append(f"  ├─ GENERATION {rec['name']} (model={rec['model']})")
            lines.append(f"  │    output: {json.dumps(rec['output'])}")
        elif rec["type"] == "span":
            lines.append(f"  ├─ SPAN {rec['name']}")
            lines.append(f"  │    input:  {json.dumps(rec['input'])}")
            lines.append(f"  │    output: {json.dumps(rec['output'])}" + (f"  ERROR {rec['error']}" if rec.get("error") else ""))
        elif rec["type"] == "trace_end":
            lines.append(f"  └─ OUTPUT {json.dumps(rec['output'])}")
            lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id", nargs="?")
    ap.add_argument("--turn", help="turn_id, e.g. outlook_as_of:t3")
    ap.add_argument("--trace-dir", default=str(TRACE_DIR))
    args = ap.parse_args(argv)
    if not args.run_id:
        for p in sorted(Path(args.trace_dir).glob("*.jsonl")):
            print(p.stem)
        return 0
    sys.stdout.reconfigure(encoding="utf-8")
    print(render(load(args.run_id, args.trace_dir), args.turn))
    return 0


if __name__ == "__main__":
    sys.exit(main())
