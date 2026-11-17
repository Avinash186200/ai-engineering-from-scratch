# 3. Architecture evolution

**Public repo:** this course, [arch_evolution/](../arch_evolution/README.md).

## The problem

An AI assistant starts with a regex router, then a classifier, then an agent loop. Each step fixes the last one's
problem and adds a new cost. Teams jump to the "modern" stage and assume it is better.

## What went wrong

On 46 hard router labels, the old rules + classifier router scored **95.7%**. The new agent loop, driven by a
keyword-only offline model, scored **69.6%**. The newer architecture lost.

## The fix

Keep the old router as a **measured baseline**, off the request path. Add the stages that make the loop safe:
verification (code renders numbers), pinned tool contracts, bounds from data, honest evals and fail-closed config.
All eight stages, each with its problem, change, trade-off and "when not to", are in
[arch_evolution/README.md](../arch_evolution/README.md).

## How to spot it next time

- A redesign has no before/after number on the same eval set.
- The old system was deleted instead of kept as a baseline.
- The model behind the new design is weaker than the design assumes.

## Say it in an interview

> Our router worked, but every new phrasing needed new rules.
> We moved to one agent loop with typed tools, and code checks every number.
> Wrong routes stopped being silent.
> But with a weak model the agent scored 69.6% against the router's 95.7%.
> Architecture alone is not a win; the model and the evals carry it.
