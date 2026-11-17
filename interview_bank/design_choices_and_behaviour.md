# Design choices and behavioural questions

Story templates: [`system_design/star_template.md`](../system_design/star_template.md).

## "Why not X?"

### 1. Why didn't you fine-tune a model?
Prompting, tools and retrieval met the quality bar, and our facts change often and need citations. I would fine-tune
for a narrow, high-volume task where a smaller tuned model beats the big one on cost, after the cheaper options fail.

### 2. Why not use a framework for everything?
Frameworks speed up the graph and state handling, so I use one there. I keep provider calls, tool contracts and
evals in my own thin code so I control behaviour and can change pieces without a rewrite.

### 3. Why not a multi-agent system?
One agent with good tools was enough and is cheaper and easier to test. I would split when evals show distinct jobs
failing in one agent, or when jobs need different permissions.

### 4. Why Postgres for state instead of a separate store?
One database for checkpoints, metadata and often vectors (pgvector) means fewer systems to run and back up. A
dedicated vector database or cache comes in when scale or latency demands it.

### 5. Why separate services instead of one app?
Separate when parts scale, deploy or fail differently (for example the tool server and the chat API). Otherwise one
app is simpler, and that is where I would start.

### 6. Why a VM, managed containers or Kubernetes?
Managed containers for most stateless services: little operations work. A VM when you need long processes or full
control. Kubernetes when you already have many services and a team to run it.

### 7. What would you do differently?
Build the golden set and tracing on day one instead of after the first bugs, and write tool contracts before tools.

### 8. What is next on your roadmap?
Name two concrete items with the reason, for example a semantic cache because of repeated questions, and online
groundedness checks because offline evals miss new failures.

## Behavioural

### 9. Tell me about a disagreement in a review.
Explain the rule behind your position, listen for the case you missed, check whether the same issue exists
elsewhere, and agree on the fix. End with what you both adopted.

### 10. How do you keep code quality high on a fast project?
Automate the checks (types, lint, tests, contract tests, eval gate) so speed does not depend on memory; small pull
requests; a short written plan for risky changes.

### 11. Tell me about finding a serious problem others missed.
Pick a case where checking carefully (a leak, a wrong date, a permission gap) changed a decision. Say how you found
it, how you raised it, and what changed after.

### 12. A question you cannot answer.
Say you do not know, reason aloud from what you do know, and say how you would find out. That is a strong answer.

### 13. How do you work with stakeholders who want results fast?
Agree what "done" means early, show work in small steps, and report uncomfortable numbers early with options.

### 14. Where do you want to grow?
Name one direction tied to the role, for example evaluation of agents at scale or serving open models, and what you
have done towards it already.
