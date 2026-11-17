# Shipping a change safely: a rollout checklist

Use it two ways: as a real checklist before a release, and as the outline of your answer when an interviewer asks
"How do you ship to production without breaking things?"

## Before the release

- [ ] The change went through a pull request with review, and CI is fully green: lint, types, unit tests,
      API contract tests and the eval gate (`day06_evals/eval_harness.py`).
- [ ] You ran the real user path on a staging environment and read the output. "No errors" is not the same as
      "correct answer".
- [ ] You read the whole current configuration of the target environment, not only the keys you plan to change.
- [ ] A written plan exists: steps, owner, how you will verify, and the exact rollback command.
- [ ] A backup or snapshot is taken. The previous image is still available, so rollback is a redeploy, not a rebuild.
- [ ] Secrets come from environment variables or a secrets manager. Logs never print values, even on error paths.
- [ ] Database changes are backward compatible (add a column first, remove the old one in a later release).

## During the release

- [ ] Pre-check the target: right environment, enough disk, services healthy, database reachable.
- [ ] Make the smallest reversible step. If you can, deploy with no traffic, run a smoke test, then send a small
      share of traffic (a canary, see `day13_cloud/canary.py`).
- [ ] Post-check: one real request end to end, one request that should fail cleanly, health endpoint green.
- [ ] Confirm the exact running version (image digest or commit), not just the tag name.

## After the release

- [ ] Watch the first hour: error rate, p95 latency, token spend per request, tool-call failures.
- [ ] The next day, read a sample of real traces for wrong-tool or ungrounded answers.
- [ ] Write down anything that surprised you and turn it into a test or a standing rule.

## Roll back when

- Error rate or p95 latency is worse than the agreed threshold.
- The golden-set score drops.
- Any data-correctness issue appears (stale data, wrong date handling). Roll back first, find the cause second.

## A story shape to tell

Pick a real incident of your own and tell it in four beats: what changed, what broke downstream, how you rolled
back and found the cause, and the rule you adopted. A common one: a bulk data load filled a column in a way a
downstream reader did not expect, and a report went blank. The lasting rule: before writing to shared tables,
list every reader of those columns and test each one.
