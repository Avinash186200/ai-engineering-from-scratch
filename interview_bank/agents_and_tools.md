# Agents and tools

Code to back these answers: `day03_agents/agent.py`, `day04_mcp/`, `day16_security/tool_policy.py`.
Worked designs: [`system_design/02_forecast_copilot.md`](../system_design/02_forecast_copilot.md),
[`system_design/04_support_triage_agent.md`](../system_design/04_support_triage_agent.md).

### 1. Why an agent instead of a simple chatbot?
Because questions need different capabilities: some need a tool, some need documents, some need both, some must
be refused. An agent decides per question. If every question took the same path, a fixed workflow would be
cheaper and easier to test.

### 2. What is tool calling at the API level?
You send tool names, descriptions and JSON schemas. The model replies with a tool name and arguments instead of
text. Your code runs the tool and sends the result back; the model then answers or calls another tool. The model
never runs anything itself.

### 3. How do you design a good tool for an LLM?
One clear purpose, a name and description that say when to use it, typed and validated inputs, compact structured
output with units and dates, and helpful error messages the model can act on.

### 4. How do you stop the model inventing numbers?
All numbers come from tools; the prompt says so; a post-check compares numbers in the answer with tool results
from this turn and blocks or flags mismatches.

### 5. What is MCP, and why use it?
The Model Context Protocol is a standard way to expose tools, data and prompts to LLM apps. Write the tool server
once and any compatible host can discover and call it, which avoids one-off integrations per app.

### 6. MCP versus plain function calling versus a REST API?
Function calling is how one model asks for one tool in one app. REST is a general service interface every caller
codes by hand. MCP standardises discovery and calls across hosts. Many systems use all three: MCP for agents, a
REST gateway for spreadsheets and scripts.

### 7. How does the agent pick a tool?
From the tool descriptions and the conversation. So descriptions matter as much as prompts. You measure
tool-selection accuracy on a golden set and fix descriptions when it drops.

### 8. What stops the agent looping forever?
A step limit, a token or cost budget per request, a timeout, and detection of the same tool call repeated with the
same arguments. When a limit trips, return what you have with a clear message.

### 9. What happens when a tool fails?
Return the error as data with a useful message; let the model retry once with corrected arguments or explain the
problem to the user. Retries with backoff for transient errors happen in code, not by the model.

### 10. Nodes, edges and state in LangGraph?
Nodes are steps (call the model, run tools). Edges connect them, and conditional edges choose the next step from the
state. State is a typed object passed along, with reducers that say how updates merge (for example, append messages).

### 11. How do you handle follow-up questions?
Keep the thread's messages in a checkpointed state store, keyed by thread id. Each turn loads the history, so "and
for last month?" makes sense. Summarise old turns when the thread gets long.

### 12. How do two users stay isolated?
Separate thread ids tied to the authenticated user, checked on every load. Memory and caches are keyed by user, and
tools receive the user identity from the server, never from the model.

### 13. What should the system refuse?
Anything outside its purpose or authority: personal advice, actions it has no right to take, requests to reveal its
instructions. Refusals are a tested route with a polite, consistent answer.

### 14. How do you add a new tool safely?
Write its contract and tests, add golden cases that need it and cases that must not use it, check tool selection on
the existing set does not drop, and release behind a flag.

### 15. Where would you put a human in the loop?
Before actions that cost money, change data or are hard to undo, and when the model's confidence or a check fails.
The graph pauses with saved state and resumes after approval.

### 16. Single agent or several agents?
Start with one agent and tools: cheaper, easier to debug. Move to a supervisor with specialists only when the jobs
truly differ (tools, permissions, parallel work) and evals show one agent failing.
