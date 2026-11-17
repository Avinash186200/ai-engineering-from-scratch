# Cheat sheet: how AI assistant architecture evolves

| # | Stage | Fixes | Costs | Skip it when |
|---|---|---|---|---|
| 1 | Regex / keyword router | nothing yet: a fast start | new rule per phrasing; silent wrong routes | users type unpredictable free text |
| 2 | Intent classifier | paraphrases rules miss | labelled data; still a second brain | no labels, tool list changes weekly |
| 3 | One agent loop, typed tools | router-model disagreement | routing = model quality | model is weak and intents are few |
| 4 | Verifier + code renders numbers | invented numbers | one more tool; report-style answers | no facts or numbers in answers |
| 5 | Pinned contracts, version admission | silent schema changes | a reviewed diff per change | solo prototype, nobody depends on you |
| 6 | Bounds from data | limits picked by feel | re-measure on model change | no eval set yet |
| 7 | Honest evals | flakiness, over-fitting, untraceable claims | eval time, live cost | never skip |
| 8 | Fail-closed config | forgotten settings weaken prod | one explicit dev line | throwaway notebook |

## My numbers (own repos; "offline" = keyword-only scripted model)

- Router on 46 hard labels: rules 84.8%, rules + classifier **95.7%**, agent offline **69.6%**.
- 30-question end-to-end set: 30/30 for router and agent offline; pass^3 30/30, 18 dev / 12 held out, 0 flaky.
- Serving router: 28% cheaper than always-large, p50 4.80 s to 2.62 s, but 15% of queries under-served.
- Bounds: measured max 3 model calls, ~4,500 tokens over 38 offline runs; shipped 5 calls, 14,000 tokens.
- Rule for bounds: tool calls 2x the largest seen, model calls the largest seen + 2, tokens 3x the largest.

## Five rules

1. **Architecture alone is not a win.** The model and the evals carry it.
2. **Keep what you remove as a baseline.** Measure the cost of every deletion.
3. **Checks in code, not in the prompt.** The model writes tokens; code checks and renders numbers.
4. **Gate on pass^k on a held-out split.** One pass on the dev set is a demo, not an eval.
5. **Unset means prod.** A mistake should only make the system stricter.

## One-line answers

- *Why delete the router?* Two brains disagree and wrong routes are silent; one loop lets the model recover.
- *Isn't 69.6% a regression?* Yes, with a weak model. That is why the baseline stays in the report.
- *How do you stop invented numbers?* The model never types digits; tokens, set lookups, code renders.
- *How do you pick a step limit?* Measure on the eval set, apply a written rule, re-derive per model.
