# 9. Debugging production surprises

**Public repo:** this course. The checks behind these habits are in
[day13_cloud/smoke_test.py](../day13_cloud/smoke_test.py) (test the deployed thing, not your laptop) and
[day14_pipelines/](../day14_pipelines/) (time and as-of logic).

Three bugs where the code was fine and the environment lied.

## The problem

A bug report says "the server sends broken responses" or "the numbers are wrong". You reproduce it on your own
machine, and your machine is part of the problem.

## What went wrong

1. **Security software rewrote an HTTP response.** A request that should have returned a clean `401
   Unauthorized` arrived as a malformed chunked response. The HTTP library failed with a framing error, which
   looked like a server bug. The cause was antivirus software on the laptop that inspects web traffic. It
   rewrote the 401 before the code saw it. The server was fine.
2. **Same model, same data, different numbers.** A statistical volatility model gave different estimates on a
   Windows laptop than on Linux in production. The optimiser and the numeric libraries differ by platform, and
   an iterative fit can land in a slightly different place.
3. **A time gate that silently used UTC.** A script was meant to stop at a local evening cut-off. In one shell,
   the named timezone was not recognised, and the shell fell back to UTC without an error. The gate was off by
   hours.

## The fix

1. **Reproduce on a clean machine first**: a container, a CI runner or a cloud shell, with no security software
   in the path. Only then call it a server bug. Compare raw bytes with `curl -v` from both places.
2. **Compute evidence in the production-like environment.** Any number that goes into a review, a report or a
   decision is produced in the Linux container or CI, not on the laptop. Pin library versions and seeds.
3. **Verify time gates by printing the resolved time and offset**, not the name you asked for. Prefer explicit
   offsets or a tested timezone library, and add a test that runs the gate at a known instant.

## How to spot it next time

- The bug reproduces on one machine only.
- An error mentions framing, chunking or a TLS problem on a response that should be simple.
- Numbers differ in a late decimal place, or more, between laptop and CI.
- A timestamp printed in "local time" looks the same as UTC.

## Say it in an interview

> A response that should have been a clean 401 arrived broken on my laptop.
> It looked like a server bug, but antivirus software was rewriting the response.
> We now reproduce on a clean machine first, and compute any evidence numbers in the production container.
> The same habit caught a model giving different numbers on Windows and Linux, and a shell that silently used UTC.
> It costs a few minutes per bug, and it has saved me from fixing the wrong thing.
