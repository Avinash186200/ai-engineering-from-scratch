# Design 2: a copilot over live forecasting models

**Prompt**: "A retail company has demand-forecast models for every store and product. Planners want to ask in plain
English: 'What is next month's forecast for umbrellas in the north region, and why did it change?'"

## 1. Clarify (assumed answers)

- Users: 300 planners, office hours, about 3,000 questions a day.
- The models run in a batch job every night and also expose a function that scores on request.
- Numbers must be exactly what the model says. A plausible but invented number is worse than no answer.
- Some planners use spreadsheets and notebooks, not chat.

## 2. Requirements

- Functional: fetch forecasts, compare periods, explain drivers, answer "what does this metric mean" from documentation.
- Non-functional: every number traceable to a model run; answers under 5 s; same numbers in chat, spreadsheet and notebook.
- Out of scope, refused politely: placing orders, changing prices.

## 3. Boxes

```
Chat UI / spreadsheet / notebook
        -> API -> agent (routing + tool calling, state per thread in Postgres)
                    -> tool server: get_forecast, compare_forecasts, top_drivers, model_info (read-only)
                    -> docs retriever: metric definitions, model documentation
                    -> LLM
        spreadsheet and notebook call the same tool server through a REST gateway
```

## 4. Deep dive: tool contracts, grounding and parity

- **Numbers only from tools**: the system prompt forbids generating figures; a post-check confirms every number in
  the answer appears in a tool result from this turn.
- **A good tool contract**: a narrow purpose, a clear description (it is effectively a prompt), typed inputs
  (`store`, `product`, `as_of` date, `horizon`), and a structured output that includes the as-of date, the model
  version, units and any caveat. Errors are explicit and helpful: "No forecast for that store; did you mean ...?"
- **Point-in-time questions**: every tool takes an `as_of` date so a planner can ask what the model said last month,
  not only what it says now.
- **Routing**: questions about numbers go to tools, questions about meaning go to documents, some need both.
  A cheap classifier or the agent's tool choice handles it; refusals are a route too.
- **Parity**: a nightly test calls the tool and the original model code on the same inputs and fails if outputs
  differ beyond rounding. This is what makes people trust the copilot.
- **One tool server, many front ends**: exposing tools through a standard protocol (such as MCP), plus a REST gateway,
  means the chat agent, the spreadsheet and the notebook all read the same numbers.

## 5. State, security, operations

- Thread state checkpointed in Postgres so any replica can continue a conversation; long threads summarised.
- Read-only tools; service account with least privilege; per-user rate limits; audit log of tool calls.
- Golden set covers each tool, each refusal and bad inputs (unknown store, future date); parity test in CI; traces
  record tool name, arguments and latency.

## 6. Trade-offs and v1

- v1: four tools, one agent with a step limit, documentation retrieval, chat only.
- Next: spreadsheet and notebook through the gateway, a "why did it change" tool that diffs drivers between runs.
- Trade-off: one agent with tools is easier to test and cheaper than several agents; split only if evals show one
  agent failing at distinct jobs.

## Likely probes

- "How do you prove the copilot's number equals the model's?" The parity test, plus the model version and as-of date
  in every answer.
- "The model is slow." Serve the nightly batch results for standard queries; call the live scorer only for custom ones.
- "Someone asks the copilot to place an order." Refusal route, logged; no write tools exist, so it cannot.
