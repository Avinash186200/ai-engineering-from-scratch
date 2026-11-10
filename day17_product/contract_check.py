"""Block breaking API changes in CI by diffing the OpenAPI schema against a committed snapshot.

Non-breaking (allowed):  new endpoint, new optional parameter, new field in a response
Breaking (blocked):      removed endpoint, removed or renamed response field, changed field type,
                         new REQUIRED parameter, removed parameter
If a change is breaking, put it in a new version (/v3) instead, or bump the major version on purpose.

Run:  python day17_product/contract_check.py              (compare live app vs snapshot)
      python day17_product/contract_check.py --update     (accept the current schema as the new snapshot)
      python day17_product/contract_check.py --selftest
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SNAPSHOT = Path(__file__).parent / "openapi_snapshot.json"


def _props(schema: dict, comps: dict) -> dict:
    if "$ref" in schema:
        schema = comps[schema["$ref"].split("/")[-1]]
    return schema.get("properties", {})


def breaking_changes(old: dict, new: dict) -> list[str]:
    out = []
    oc, nc = old.get("components", {}).get("schemas", {}), new.get("components", {}).get("schemas", {})
    for path, ops in old["paths"].items():
        if path not in new["paths"]:
            out.append(f"removed endpoint {path}")
            continue
        for method, op in ops.items():
            nop = new["paths"][path].get(method)
            if nop is None:
                out.append(f"removed {method.upper()} {path}")
                continue
            oparams = {p["name"]: p for p in op.get("parameters", [])}
            nparams = {p["name"]: p for p in nop.get("parameters", [])}
            out += [f"{path}: removed parameter '{n}'" for n in oparams.keys() - nparams.keys()]
            out += [f"{path}: new required parameter '{n}'" for n, p in nparams.items()
                    if n not in oparams and p.get("required")]
            osch = op.get("responses", {}).get("200", {}).get("content", {}).get("application/json", {}).get("schema")
            nsch = nop.get("responses", {}).get("200", {}).get("content", {}).get("application/json", {}).get("schema")
            if osch and nsch:
                out += _diff_fields(path, osch, nsch, oc, nc)
    return out


def _diff_fields(where, osch, nsch, oc, nc, depth=0) -> list[str]:
    out = []
    op_, np_ = _props(osch, oc), _props(nsch, nc)
    for name, spec in op_.items():
        if name not in np_:
            out.append(f"{where}: removed response field '{name}'")
            continue
        if spec.get("type") != np_[name].get("type"):
            out.append(f"{where}: field '{name}' type {spec.get('type')} -> {np_[name].get('type')}")
        if spec.get("type") == "array" and depth < 3:
            out += _diff_fields(f"{where}.{name}[]", spec.get("items", {}), np_[name].get("items", {}), oc, nc, depth + 1)
    return out


def current_schema() -> dict:
    from day17_product.service import app
    return app.openapi()


def _selftest() -> None:
    base = current_schema()
    renamed = copy.deepcopy(base)
    row = renamed["components"]["schemas"]["RowV1"]["properties"]
    row["predicted_return_decimal"] = row.pop("predicted_return")
    added = copy.deepcopy(base)
    added["components"]["schemas"]["RowV1"]["properties"]["confidence"] = {"type": "number"}
    print("rename a v1 field ->", breaking_changes(base, renamed))
    print("add a v1 field    ->", breaking_changes(base, added) or "no breaking changes")
    assert breaking_changes(base, renamed) and not breaking_changes(base, added)
    print("ok: renames are blocked, additions are allowed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    elif "--update" in sys.argv:
        SNAPSHOT.write_text(json.dumps(current_schema(), indent=1, sort_keys=True))
        print("snapshot updated:", SNAPSHOT.name)
    else:
        problems = breaking_changes(json.loads(SNAPSHOT.read_text()), current_schema())
        for p in problems:
            print("BREAKING:", p)
        print("contract ok" if not problems else f"{len(problems)} breaking change(s)")
        sys.exit(1 if problems else 0)
