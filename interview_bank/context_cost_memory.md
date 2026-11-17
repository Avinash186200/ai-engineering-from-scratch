# Context, cost and memory

More on memory, caching and routing in [`interview_special/`](../interview_special/README.md).

### 1. What is context engineering?
Deciding what goes into the model's context on each call: instructions, the relevant history, retrieved passages,
tool results and tool definitions, in a sensible order and within a budget. Most quality problems in agents are
context problems, not model problems.

### 2. How do you manage a context window that keeps growing?
Keep the system prompt and recent turns verbatim, summarise older turns, store large tool outputs outside the
context and pass a short summary or a handle, and load only the tools relevant to the current step.

### 3. Users ask the same things repeatedly. How do you cut cost but keep context?
Three layers: prompt caching for the stable prefix; an exact-match cache for identical requests; a semantic cache
for close paraphrases, with a strict similarity threshold and the user's permissions in the key. Never cache answers
that depend on fresh data without an expiry.

### 4. How do you route requests to different models by difficulty?
A cheap classifier or rules (length, intent, need for tools) send easy requests to a small model and hard ones to a
large one. A cascade tries the small model first and escalates when a check fails. Measure quality and cost per route.

### 5. How do you design memory at user and organisation level?
Short-term memory is the thread state. Long-term memory is small notes (preferences, facts, past decisions) with
embeddings, stored in namespaces: per user, and per organisation. Retrieve only the notes relevant to the question.
User notes never move into the shared space without an explicit rule or approval.

### 6. How do you drop irrelevant or stale memory?
Give notes a timestamp and a source, decay or expire them, let new facts overwrite old ones about the same subject,
and let users view and delete what is remembered.

### 7. How do you put a cost ceiling on an agent?
A token budget per request and per user per day, a step limit, cheaper models for sub-steps, and alerts on cost per
completed task, which catches loops and retries that cost per request hides.

### 8. How do you reduce latency?
Stream the answer, run independent tool calls in parallel, cache, use a smaller model for routing, keep prompts
short, and put the service near the model provider's region. Measure each step in traces before optimising.
