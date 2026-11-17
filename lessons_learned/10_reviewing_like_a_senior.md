# 10. Reviewing code like a senior

**Public repo:** this course, [day11_git_docker/](../day11_git_docker/) (pull requests, CI and review flow) and
[day15_testing/](../day15_testing/) (tests that make a review cheaper).

## The problem

A junior review reads the diff and checks style. The defects that hurt live outside the diff: in the sibling
file, in the reply that promised a fix, in the PR that lands next week.

## What went wrong

These are patterns I have seen, and missed, in real reviews.

- **The same defect in a second file.** A bug was fixed in one module. The sibling module, written from the same
  template, had the same bug and nobody looked.
- **The reply did not match the code.** "Fixed in the latest commit" was the reply. The commit fixed half of it.
- **Dead switches.** A config flag was added and documented, but no code path read it. Turning it off did nothing.
- **Cross-PR coupling.** Two open PRs each passed CI alone. Merged together, one broke the other's assumption.
- **Pending decisions lost.** A reviewer asked a design question, and the PR merged before anyone answered.
- **Reading only the verdict.** An "approve" review carried non-blocking notes that nobody turned into follow-ups.
- **Approving too early.** An approval was given while CI was still running, or before the newest commit.

## The fix

A checklist I run before any approval:

1. For each defect found, grep the repo for the same pattern in sibling files.
2. For each "fixed" reply, open the commit and check the claim line by line.
3. For each new flag or setting, find the code that reads it, and test both values.
4. List the other open PRs that touch the same files or contracts.
5. Keep a list of open questions; none may be silently dropped.
6. Read every review in full, including approvals. Every non-blocking note becomes a tracked follow-up.
7. Approve only when the CI run for the latest commit is green and no blocker is open.

## How to spot it next time

- A fix touches one file out of several that look alike.
- A reply says "done" and the diff is smaller than the request.
- A flag appears in docs and config but in no `if` statement.
- Two PRs edit the same interface in the same week.
- The approval time is older than the latest commit.

## Say it in an interview

> Early on, I reviewed only the diff, and I missed the same bug in a sibling file.
> Now I grep for the same pattern, check each "fixed" reply against the code, and look for flags nothing reads.
> I also check other open PRs that touch the same files, and keep open questions on a list.
> Reviews got slower per PR, but fewer bugs came back after merge.
> It does not replace tests; it finds what tests were never written for.
