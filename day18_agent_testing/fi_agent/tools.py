"""Three fake, deterministic tools. Data is 'as of' a snapshot date.

SNAPSHOT_DATE is the last complete daily snapshot.
LATEST_AVAILABLE is a newer, partial (intraday) load. Using it by mistake
is the classic 'silently answered from the wrong date' bug.
"""

SNAPSHOT_DATE = "2026-11-13"
LATEST_AVAILABLE = "2026-11-14"   # partial load, not a complete snapshot

# (as_of, horizon_days) -> outlook
_OUTLOOK = {
    ("2026-11-12", 5):  {"rate_change_bp": -3.1, "spread_change_bp": 1.4, "confidence": 0.62},
    ("2026-11-12", 21): {"rate_change_bp": -7.8, "spread_change_bp": 2.9, "confidence": 0.55},
    ("2026-11-13", 5):  {"rate_change_bp": -2.4, "spread_change_bp": 0.8, "confidence": 0.64},
    ("2026-11-13", 21): {"rate_change_bp": -6.5, "spread_change_bp": 2.2, "confidence": 0.57},
    ("2026-11-14", 5):  {"rate_change_bp": 1.7,  "spread_change_bp": -0.6, "confidence": 0.41},
    ("2026-11-14", 21): {"rate_change_bp": 3.9,  "spread_change_bp": -1.3, "confidence": 0.38},
}

# (bond_id, as_of) -> metrics
_BONDS = {
    ("POOL-A30", "2026-11-12"): {"oas_bp": 48.2, "eff_duration": 5.91, "convexity": -1.12},
    ("POOL-A30", "2026-11-13"): {"oas_bp": 47.6, "eff_duration": 5.87, "convexity": -1.09},
    ("POOL-A30", "2026-11-14"): {"oas_bp": 51.3, "eff_duration": 6.04, "convexity": -1.21},
    ("POOL-B15", "2026-11-12"): {"oas_bp": 36.9, "eff_duration": 3.42, "convexity": -0.58},
    ("POOL-B15", "2026-11-13"): {"oas_bp": 36.1, "eff_duration": 3.39, "convexity": -0.55},
    ("POOL-B15", "2026-11-14"): {"oas_bp": 38.8, "eff_duration": 3.51, "convexity": -0.63},
}


class ToolError(ValueError):
    pass


def get_snapshot_date():
    return {"snapshot_date": SNAPSHOT_DATE, "latest_available": LATEST_AVAILABLE,
            "latest_is_partial": True, "fresh": False, "age_days": 5}


def get_outlook(horizon_days, as_of):
    if horizon_days not in (5, 21):
        raise ToolError("horizon_days must be 5 or 21")
    key = (as_of, horizon_days)
    if key not in _OUTLOOK:
        raise ToolError(f"no outlook for as_of={as_of}")
    return {"as_of": as_of, "horizon_days": horizon_days, **_OUTLOOK[key]}


def get_bond_metrics(bond_id, as_of):
    key = (bond_id, as_of)
    if key not in _BONDS:
        raise ToolError(f"no metrics for {bond_id} as_of={as_of}")
    return {"bond_id": bond_id, "as_of": as_of, **_BONDS[key]}


TOOLS = {
    "get_snapshot_date": get_snapshot_date,
    "get_outlook": get_outlook,
    "get_bond_metrics": get_bond_metrics,
}

# JSON schemas, used by the optional real-LLM mode.
TOOL_SCHEMAS = [
    {"name": "get_snapshot_date", "description": "Return the date of the latest complete data snapshot and freshness.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "get_outlook", "description": "Rate/spread outlook for a horizon, as of a snapshot date (YYYY-MM-DD).",
     "input_schema": {"type": "object", "properties": {
         "horizon_days": {"type": "integer", "enum": [5, 21]},
         "as_of": {"type": "string"}}, "required": ["horizon_days", "as_of"]}},
    {"name": "get_bond_metrics", "description": "OAS, effective duration and convexity of a bond/pool as of a date.",
     "input_schema": {"type": "object", "properties": {
         "bond_id": {"type": "string"}, "as_of": {"type": "string"}}, "required": ["bond_id", "as_of"]}},
]


def call_tool(name, params):
    return TOOLS[name](**params)
