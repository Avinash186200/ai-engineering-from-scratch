# 5. Measure, don't guess

**Public repo:** [llm-serving-patterns](https://github.com/Avinash186200/llm-serving-patterns).

## The problem

"Add a semantic cache" and "route easy queries to a small model" are easy to say. Each has a number behind it:
hits, wrong answers served, money saved, quality lost.

## What went wrong

The obvious settings each hid a cost that only a benchmark showed.

- **Cache threshold.** With MiniLM at 0.80, the hit rate was 44.9%, but 6.6% of all queries got a wrong cached
  answer. The near-misses were the same question about a different entity ("on iOS" vs "on Android").
- **Router.** Rules + classifier cost 28% less than always-large and cut p50 latency from 4.80 s to 2.62 s, but
  15% of queries landed on a model that was too small.
- **Memory.** A sliding window drops facts the moment they fall out. Full history works and grows without limit.
- **Resilience.** Plain retries took success from 65% to 94%, but made more calls per request.

## The fix

- Start the cache at a strict threshold (0.90: 20.7% hit rate, 0.000 false hits), log near-misses, and lower it
  only after labelling them. Add an entity check before serving a semantic hit.
- Gate every router change on a labelled eval set with a minimum task-success bar, not just accuracy.
- Vector recall kept the fact in the prompt in every test, at 13x fewer tokens than full history.
- Retry + circuit breaker + fallback reached 99.9% success with fewer calls than plain retry (1.17 vs 1.32 per
  request), because the breaker stops calls to a provider that is down.

## How to spot it next time

- A claim like "the cache saves money" with no false-hit rate next to it.
- A router judged on cost alone.
- A memory test where the question shares words with the fact. That is easy for vector recall. Updated facts
  ("actually I moved") are where it fails, and that is not tested yet.

## Say it in an interview

> Everyone says add a semantic cache, so I measured it.
> At a 0.80 threshold, 6.6% of queries got a wrong answer from the cache.
> We started at 0.90, where false hits were zero, and logged near-misses before lowering it.
> The router saved 28%, but 15% of queries went to a model that was too small, so we gate it on evals.
> The model calls were simulated, so the shape transfers, not the exact numbers.
