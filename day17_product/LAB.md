# Day 17 lab: serve one model to an agent, Excel, notebooks and services

Run from the repo root. No API key or server needed for the self-tests.

## Step 1: one model, two contract versions
```bash
python day17_product/service.py
```
`/v1/rank` (frozen, marked deprecated, with `Deprecation` and `Sunset` headers) and `/v2/rank` (explicit units,
model version, as-of date used) return the **same fund**, because both call the same `rank_funds` function that the
agent's MCP tool calls (`day04_mcp/fund_mcp_server.py`). One implementation, many channels: answers never disagree.

## Step 2: run it and read the docs
```bash
uvicorn day17_product.service:app --port 8010
```
Open http://localhost:8010/docs: every endpoint, parameter and response schema, generated from the code.
Use "Try it out" on `/v2/rank` and fill the `x-api-key` field with `demo-key-excel-team`. Then try:
```bash
curl -H "X-API-Key: demo-key-excel-team" "http://localhost:8010/v2/rank.csv?as_of=2025-06-19&top_n=5"
```

## Step 3: the notebook client
```bash
python day17_product/client.py
```
Two simulated 503s are retried with backoff (1 s, 2 s); a bad date (422) and a bad key (401) are **not** retried and come
back as a typed `ModelAPIError`. In a notebook: `ModelClient(url).rank_df("2025-06-19")` gives a DataFrame.

## Step 4: Excel
Open `excel_power_query.m` and follow the comments: define named cells `AsOf` and `ApiKey`, paste the query into the
Advanced Editor, load it. Refresh pulls new numbers from the same model the assistant uses, with `model_version` and
`as_of_used` columns so every sheet shows what produced it.

## Step 5: stop breaking changes in CI
```bash
python day17_product/contract_check.py --selftest
python day17_product/contract_check.py
```
Renaming a v1 field is reported as breaking; adding a field is fine. In CI this exits 1 on a breaking change.
Try it for real: rename `predicted_return` in `RowV1` in `service.py`, run the check, then undo.

## Step 6 (exercise): add v3 the right way
Add `/v3/rank` that also returns a `confidence` field. Keep v1 and v2 unchanged, run the contract check (should pass),
then `--update` the snapshot and commit it with the code.

## Product checklist for a model API
| Question | Answer in this repo |
|---|---|
| Do all channels give the same answer? | One function behind MCP, REST and CSV |
| Can old clients keep working? | `/v1` frozen; breaking changes go to a new version; contract check in CI |
| Are units and meaning explicit? | `predicted_return_pct`, `as_of_used`, `model_version`, caveat |
| Who is calling, how much? | API key per client, usage counted, revocable |
| Do errors help the caller? | Typed `{code, message}`, never a stack trace |
| How are clients told about changes? | `Deprecation`, `Sunset`, `Link` headers, then a changelog |
