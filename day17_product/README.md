# Day 17: Models as a product

A model is only useful if people can use it where they work. This day serves one model to an AI agent (MCP), to Excel
(Power Query / CSV), to notebooks (a small client) and to other services (REST + OpenAPI), with versioned contracts,
explicit units, API keys per client, typed errors, deprecation headers and a CI check that blocks breaking changes.

| File | What it is |
|---|---|
| [service.py](service.py) | FastAPI model API: frozen `/v1`, explicit `/v2`, CSV for spreadsheets, keys per client, deprecation headers |
| [client.py](client.py) | Python client for notebooks: retries with backoff on 429/5xx only, typed errors, DataFrame helper |
| [excel_power_query.m](excel_power_query.m) | Power Query script: Excel pulls rankings from the API, with model version and as-of date |
| [contract_check.py](contract_check.py) | Diffs the OpenAPI schema against a committed snapshot; fails CI on breaking changes |
| [openapi_snapshot.json](openapi_snapshot.json) | The committed contract |
| [LAB.md](LAB.md) | Six steps and a product checklist |
| [INTERVIEW_QA.md](INTERVIEW_QA.md) | Interview questions with full explanations and spoken answers |

The agent channel is the Day 4 MCP server (`day04_mcp/fund_mcp_server.py`), which calls the same function.

## Quick start
```bash
python day17_product/service.py
python day17_product/client.py
python day17_product/contract_check.py
```

## Five lessons from a real production AI platform
1. Expose the model once and put gateways in front: the agent used MCP, Excel users got the same tools through an
   MCP-to-REST gateway, notebooks called the same API. One source of truth.
2. Analysts live in spreadsheets. A model that only works in a chat window has few users.
3. Units and dates belong in the contract. A percentage that silently becomes a decimal is a production incident.
4. Version client software too: the spreadsheet add-in shipped as numbered releases, tested in UAT before anyone got it.
5. Keep the LLM layer vendor-neutral behind your own adapter, so switching providers is a config change.
