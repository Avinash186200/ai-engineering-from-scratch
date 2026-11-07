# Interview questions: Git, GitHub, CI/CD, Docker

For each question: open **Understand it** and read until it is clear, then say the **Answer** out loud in 30-45 seconds.


## Git basics

### 1. What is Git, and how is it different from GitHub?

<details><summary>Understand it</summary>

```text
WHAT GIT IS
Git is a version control system: a program on your computer that records snapshots ('commits') of your project over time. Each commit stores what changed, who changed it, when, and a message saying why. You can go back to any snapshot, compare versions, and work on several lines of change in parallel (branches).

KEY PROPERTY: DISTRIBUTED
Every clone has the FULL history. You can commit, branch and view history offline. There is no single point of failure.

WHAT GITHUB IS
GitHub is a website/service that hosts a shared copy of Git repositories ('remote') and adds team features on top:
- Pull requests (proposed changes + discussion + review)
- Code review with line comments and approvals
- Issues (task/bug tracking)
- GitHub Actions (CI/CD automation)
- Permissions, branch protection, secret storage
Alternatives: GitLab, Bitbucket.

ANALOGY
Git is like the 'track changes + save points' engine on your laptop. GitHub is like Google Drive for those repositories plus a meeting room where the team reviews changes.

COMMON MISTAKE
Saying 'I pushed to Git' when you mean GitHub, or thinking Git needs internet. Commit is local; push is what talks to GitHub.
```

</details>

**Answer:** Git is a distributed version control tool that records commits of a project locally; every clone has full history. GitHub hosts a shared remote copy and adds collaboration: pull requests, reviews, issues, branch protection and GitHub Actions for CI. On our platform, all code went through GitHub PRs with CI gates and review before merge.

### 2. Explain the working directory, staging area and repository.

<details><summary>Understand it</summary>

```text
THE FOUR BOXES (learn to draw this)
1. Working directory (working tree): the actual files in your folder that you edit.
2. Staging area (index): a 'waiting room' where you put exactly the changes that should go into the next commit. Lets you commit part of your work.
3. Local repository: your commit history, stored in the hidden .git folder.
4. Remote repository: the shared copy on GitHub (usually called 'origin').

HOW CHANGES MOVE
- edit file -> working directory
- git add file -> staging area
- git commit -m "msg" -> local repository
- git push -> remote (GitHub)
- git pull / git fetch -> brings remote changes back

WHY STAGING EXISTS
You may have edited five files but only two belong to this logical change. Stage those two, commit them with a clear message; commit the rest separately. This keeps commits small and reviewable.

USEFUL COMMANDS
- git status: shows which box each change is in.
- git diff: working dir vs staging.
- git diff --staged: staging vs last commit.
- git restore --staged file: move back out of staging.
```

</details>

**Answer:** Changes live in four places: the working directory where I edit, the staging area where git add selects exactly what goes into the next commit, the local repository where git commit stores the snapshot, and the remote on GitHub that git push updates. Staging lets me keep each commit to one logical change.

### 3. Walk me through your daily Git workflow.

<details><summary>Understand it</summary>

```text
A REALISTIC DAILY FLOW
1. git switch main && git pull - start from the latest shared code.
2. git switch -c fix/typed-errors - new branch for the task.
3. Edit code; run tests locally.
4. git status / git diff - check exactly what changed.
5. git add <files> ; git commit -m "Return typed error when data is missing" - small, clear commits.
6. git fetch origin && git rebase origin/main (or merge) - bring in teammates' changes, resolve conflicts early.
7. git push -u origin fix/typed-errors - publish the branch.
8. Open a pull request (website or `gh pr create`): description with what, why, how tested.
9. CI runs; fix anything red; read the actual check results.
10. Reviewer comments -> push more commits addressing them.
11. After approval (and green CI on the LATEST commit), the maintainer merges.
12. git switch main && git pull; delete the old branch.

TEAM RULES WE FOLLOWED
- No direct pushes to main.
- One reviewer first, then the lead merges.
- Diff against the true current main before pushing.
- No pushes late at night (finish locally, push next morning) so reviewers see work at a sensible time.
```

</details>

**Answer:** I start from fresh main, create a branch per task, make small commits with clear messages, rebase or merge the latest main, push the branch and open a PR with what, why and how it was tested. CI must be green; a reviewer approves; the maintainer merges. On our platform nobody pushed to main directly — one reviewer first, then only the lead merged.

### 4. What makes a good commit and commit message?

<details><summary>Understand it</summary>

```text
A GOOD COMMIT
- One logical change (atomic). If you need 'and' to describe it, consider splitting.
- Builds and passes tests on its own (helps git bisect later).
- No unrelated formatting noise mixed with logic changes.

A GOOD MESSAGE
- Subject line (~50 chars), imperative mood: 'Return typed error when data is missing'.
- Optional body: WHY the change was needed, any trade-offs, links to issue (#25).
- Bad: 'fix', 'update', 'changes', 'wip'.

CONVENTIONS SOME TEAMS USE
Conventional Commits: 'feat: ...', 'fix: ...', 'docs: ...', 'refactor: ...' - enables automated changelogs and versioning.

WHY IT MATTERS
- Reviewers understand the change quickly.
- git log / git blame months later explain WHY code is the way it is.
- Easy to revert one specific change.

THE COMMIT HASH
Each commit has a unique SHA (e.g. 1cdf749...). Short hashes identify exact code - on our platform the production image was tagged main-1cdf749, tying the running container to an exact commit.
```

</details>

**Answer:** A good commit is one logical change that builds and passes tests on its own; the message is an imperative subject saying what changed, with a body saying why and linking the issue. It makes review, blame and reverting easy. We tagged production images with the commit hash so we always knew exactly which code was live.

### 5. What is .gitignore and what should go in it?

<details><summary>Understand it</summary>

```text
WHAT IT IS
A file listing patterns of files/folders Git should NOT track. Ignored files never show up in git status and can't be accidentally committed (unless forced).

WHAT TO PUT IN IT (AI/Python projects)
- Secrets and config: .env, *.pem, credentials.json
- Python artifacts: __pycache__/, *.pyc, .venv/, .pytest_cache/, .mypy_cache/
- Data and models: data/, *.parquet, *.csv dumps, model weights (*.pt, *.pkl) - use proper storage instead
- Logs and outputs: *.log, output/
- Editor/OS files: .vscode/, .idea/, .DS_Store
- Anything personal: email drafts, scratch notes

IMPORTANT DETAIL
.gitignore only affects UNTRACKED files. If a file was already committed, adding it to .gitignore does nothing - you must 'git rm --cached file' and commit, and if it was a secret, rotate it (it's still in history).

RELATED
- .dockerignore - same idea for Docker build context.
- Global gitignore for your own editor files.
```

</details>

**Answer:** It lists files Git must never track: env files and keys, caches like __pycache__ and virtualenvs, data dumps, model weights, logs and personal drafts. It only affects untracked files — if something was already committed you must remove it from the index, and if it's a secret, rotate it because it's still in history.


## Branching & PRs

### 6. What is a branch and why use one?

<details><summary>Understand it</summary>

```text
WHAT A BRANCH IS
A movable pointer to a commit. When you commit on a branch, the pointer moves forward. Creating a branch is instant and cheap - Git doesn't copy files.

WHY USE BRANCHES
- Isolation: work on a fix or feature without affecting main.
- Parallel work: many developers, many branches, one main.
- Review: a branch becomes a pull request; main only receives reviewed code.
- Experiments: try something; delete the branch if it fails.

MAIN
'main' (formerly 'master') is the trusted branch - deployable, protected. Branch protection rules on GitHub can require PR reviews and green CI before merge, and block force pushes.

NAMING
Descriptive: fix/typed-errors, feat/raw-data-mcp, docs/runbook. Some teams include the issue number: fix/25-raw-data.

HEAD
HEAD is Git's pointer to 'where you are now' - usually the current branch. 'Detached HEAD' means you've checked out a specific commit, not a branch; commits made there can be lost if you switch away without creating a branch.

COMMANDS
git branch (list), git switch -c name (create+switch), git switch name, git branch -d name (delete merged), git push -u origin name.
```

</details>

**Answer:** A branch is a cheap movable pointer to a commit that lets me work in isolation from main. Each change gets its own branch, which becomes a pull request; main stays protected and deployable, receiving only reviewed, green code.

### 7. What is a pull request and how does code review work?

<details><summary>Understand it</summary>

```text
WHAT A PR IS
A GitHub feature: a request to merge one branch into another (usually into main). It shows:
- The diff (every changed line)
- A description (what, why, how tested, linked issues)
- CI check results
- Review comments and approvals
- The full conversation

THE REVIEW PROCESS
1. Author opens PR, ideally small and focused, with all checks green.
2. Reviewer(s) read the diff, leave line comments: bugs, unclear logic, missing tests.
3. Review outcome: Comment / Approve / Request changes.
4. Author pushes fixes as new commits and replies to each comment.
5. After approval AND green CI on the latest commit, a maintainer merges.

MERGE OPTIONS ON GITHUB
- Merge commit: keeps all commits + a merge commit.
- Squash and merge: all PR commits become one commit on main (clean history).
- Rebase and merge: replays commits linearly.

GOOD PRACTICE
- Descriptions must be accurate: if it says 'closes #25', it must really close it.
- An approval given before your last commit doesn't cover the new code.
- Review comments may appear in three places: inline comments, review bodies, and the PR conversation - read them all.
- Draft PRs for early feedback.
```

</details>

**Answer:** A PR proposes merging a branch into main, showing the diff, description, CI results and discussion. Reviewers comment line by line and approve or request changes; the author pushes fixes; once approved with green CI on the latest commit, the maintainer merges, often by squash. In our team one reviewer reviewed first and only the lead merged.

### 8. Merge vs rebase — what's the difference and when do you use each?

<details><summary>Understand it</summary>

```text
THE SITUATION
You branched from main; meanwhile main got new commits. You need those changes in your branch.

MERGE
git merge main (while on your branch)
- Creates a new 'merge commit' with two parents, joining the histories.
- Preserves exactly what happened, including when branches diverged.
- Never rewrites existing commits -> always safe, even on shared branches.
- History can look busy (many merge commits).

REBASE
git rebase main (while on your branch)
- Takes your commits and replays them one by one on top of the latest main.
- Result: straight-line history, as if you started from the latest main.
- REWRITES your commits (new hashes). If others have your old commits, their history now diverges.
- Needs force-push afterward (use --force-with-lease, which refuses if someone else pushed).

GOLDEN RULE
Never rebase commits that others are building on (shared/public branches). Rebasing your own private feature branch is fine.

INTERACTIVE REBASE
git rebase -i lets you squash, reorder, edit commit messages before opening a PR - tidy history.

TEAM CHOICE
Many teams: rebase locally to stay current, squash-merge PRs into main. Others prefer merge commits for full traceability.
```

</details>

**Answer:** Merge joins histories with a merge commit and never rewrites anything, so it's always safe. Rebase replays my commits on top of the latest main for a linear history but rewrites hashes, so I only rebase my own private branches and push with force-with-lease. Never rebase a branch others are using.

### 9. How do you resolve a merge conflict?

<details><summary>Understand it</summary>

```text
WHEN CONFLICTS HAPPEN
Two branches changed the same lines (or one deleted a file the other edited). Git can't decide, so it stops and marks the file.

WHAT YOU SEE
<<<<<<< HEAD
TIMEOUT_SECONDS = 30          (your version / current branch)
=======
TIMEOUT_SECONDS = 60          (incoming version)
>>>>>>> fix/slow-models

STEPS
1. git status - lists conflicted files.
2. Open each file; understand WHY each side changed it (read both commits/PRs).
3. Choose one side, or combine them correctly. Delete the markers.
4. Run tests - a syntactically clean merge can still be logically wrong.
5. git add <file>, then git commit (merge) or git rebase --continue (rebase).
6. If it gets messy: git merge --abort / git rebase --abort returns to before.

TOOLS
VS Code's merge editor, git mergetool.

REDUCING CONFLICTS
- Pull/rebase from main often.
- Small, short-lived branches.
- Don't mix big reformatting with logic changes.
- Communicate when touching shared files.
```

</details>

**Answer:** Git marks both versions in the file. I check git status, understand why each side changed the code, keep or combine the right logic, delete the markers, run the tests, then git add and continue the merge or rebase. If it goes wrong, merge --abort or rebase --abort. Rebasing often and keeping branches small prevents most conflicts.

### 10. What branching strategy would you use for an AI product?

<details><summary>Understand it</summary>

```text
COMMON STRATEGIES
1. Trunk-based development: everyone works in short-lived branches (hours-days) merged into main frequently, behind CI gates and feature flags. Main is always deployable. Favoured by most modern teams.
2. GitHub Flow: main + feature branches + PRs; deploy from main. Simple; basically trunk-based with PRs.
3. Git Flow: long-lived develop, release and hotfix branches. Heavier; suits scheduled versioned releases (e.g. packaged software), less common for web services now.

FOR AN AI PRODUCT I'D CHOOSE
GitHub Flow / trunk-based:
- Feature branches -> PR -> CI (lint, types, tests, contract tests, eval harness) -> review -> merge to main.
- main builds an image tagged by commit; deploy that image to dev, then prod with approval.
- Tags (v1.2.0) for model/package releases.
- Hotfix: branch from main, same PR process (fast-tracked review).

AI-SPECIFIC ADDITIONS
- Eval harness as a CI gate: prompt or model changes must not drop answer quality.
- Version prompts in the repo.
- Model packages as separately versioned artifacts (wheels) in a registry.

REAL EXAMPLE
Models were split into separate packages (wheels) with their own repos and versions, consumed by a model-free MCP server.
```

</details>

**Answer:** Trunk-based / GitHub Flow: short-lived branches, PRs with CI gates including an eval harness, review, merge to an always-deployable main, build an image per commit, deploy to dev then prod with approval, and tag releases. Model code can live as separately versioned packages, like our split into a model-free MCP server plus model wheels.


## History & undo

### 11. How do you undo changes in Git? (restore, reset, revert)

<details><summary>Understand it</summary>

```text
PICK BY SITUATION

1. Discard uncommitted edits to a file
   git restore file.py           (old: git checkout -- file.py)

2. Unstage a file (keep the edits)
   git restore --staged file.py

3. Fix the last commit (not yet pushed)
   git commit --amend            (change message or add forgotten file)

4. Undo commits LOCALLY (not pushed)
   git reset --soft HEAD~1   -> undo commit, keep changes staged
   git reset --mixed HEAD~1  -> undo commit, keep changes unstaged (default)
   git reset --hard HEAD~1   -> undo commit AND throw away changes (destructive!)

5. Undo a commit that is ALREADY PUSHED / shared
   git revert <hash>  -> creates a NEW commit that reverses it. History stays intact; safe for everyone.

6. Park work temporarily
   git stash / git stash pop

7. Recover 'lost' commits
   git reflog - shows every position HEAD has been, even after reset; you can get back to them.

THE RULE
Rewrite history (reset, amend, rebase) only for commits nobody else has. For shared commits, revert.
```

</details>

**Answer:** Restore discards or unstages file edits; amend fixes the last unpushed commit; reset moves my branch back locally — soft keeps changes staged, hard throws them away; revert creates a new commit undoing a pushed one, which is the safe choice for shared history; reflog recovers commits I thought I'd lost.

### 12. You accidentally committed an API key. What do you do?

<details><summary>Understand it</summary>

```text
STEP 1: ROTATE THE KEY IMMEDIATELY (most important)
Assume it's compromised the moment it was pushed. Revoke/regenerate it at the provider. Deleting it from the code does NOT help: it's still in history, and every clone and fork has it. Bots scan GitHub for keys within minutes.

STEP 2: REMOVE IT FROM HISTORY
- Tools: git filter-repo or BFG Repo-Cleaner to rewrite history removing the file/string.
- Force-push the cleaned history; teammates must re-clone or reset.
- GitHub may still have cached views/PR refs - contact support if needed.

STEP 3: CHECK FOR MISUSE
Review the provider's usage logs for the window it was exposed.

STEP 4: PREVENT
- .gitignore for .env and key files.
- Secrets in env vars / secrets manager, never in code.
- Secret scanning: GitHub secret scanning + push protection, pre-commit hooks (gitleaks, detect-secrets).
- Never print secrets in logs (e.g. don't print env vars by name pattern - DATABASE_URL contains the password).

IF NOT YET PUSHED
git reset / git commit --amend to remove it before pushing - still consider rotating if unsure.
```

</details>

**Answer:** Rotate the key immediately, because deleting it doesn't remove it from history and bots scan GitHub in minutes. Then rewrite history with git filter-repo or BFG and force-push, check the provider's logs for misuse, and prevent recurrence with gitignore, secrets in env vars or a secrets manager, and secret scanning with push protection.

### 13. What's the difference between git fetch and git pull?

<details><summary>Understand it</summary>

```text
GIT FETCH
Downloads new commits and branches from the remote (origin) into your local copy of the remote branches (origin/main), WITHOUT changing your working files or your current branch. Safe, read-only from your work's perspective.

GIT PULL
= git fetch + git merge (or git rebase, if configured) into your current branch. Changes your branch.

WHY FETCH IS USEFUL
- Inspect before integrating: git fetch; git log main..origin/main; git diff main origin/main.
- Diff your work against the TRUE current main before pushing or deploying: git fetch origin && git diff origin/main.

CONFIG
git config pull.rebase true -> pull rebases instead of merging (linear history).

REAL LESSON
A refactor branch was compared against a stale local copy and missed 19 later merges on main. 'git fetch' and diffing against origin/main would have shown it immediately.
```

</details>

**Answer:** Fetch downloads remote commits into origin/* without touching my branch; pull is fetch plus merge or rebase into my current branch. I fetch first when I want to inspect or diff against the true current main — on our platform a branch compared to a stale copy had silently missed 19 merges.

### 14. How do you find which commit introduced a bug?

<details><summary>Understand it</summary>

```text
TOOLS
1. git log -p file / git log -S "text" - search history for when a line or string appeared/disappeared.
2. git blame file - who last changed each line, in which commit. Then git show <hash>.
3. git bisect - binary search through history:
   git bisect start
   git bisect bad            (current commit is broken)
   git bisect good v1.2.0    (this older one was fine)
   Git checks out the middle commit; you test and mark good/bad; repeat.
   ~log2(N) steps: 1,000 commits -> about 10 tests.
   Can be automated: git bisect run ./test.sh
   git bisect reset when done.

WHY SMALL COMMITS MATTER
Bisect points to a commit; if that commit is small and atomic, the bug is obvious.
```

</details>

**Answer:** I use git log -S or blame to find when a line changed, and git bisect for regressions: mark a bad and a good commit and Git binary-searches, so a thousand commits take about ten tests, and it can run a test script automatically. Small atomic commits make the culprit obvious.


## CI/CD & GitHub Actions

### 15. What is CI/CD?

<details><summary>Understand it</summary>

```text
CI - CONTINUOUS INTEGRATION
Every change (PR) is automatically built and tested before merge. Integrate small changes often, so problems surface immediately rather than in a big painful merge later.
Typical gates: lint, type checks, unit/integration tests, security scans, contract tests, and for AI apps an eval harness.

CD - CONTINUOUS DELIVERY / DEPLOYMENT
- Continuous Delivery: every merged change produces a release-ready artifact (e.g. Docker image) that CAN be deployed with one approved step.
- Continuous Deployment: it IS deployed automatically to production without manual approval.

THE PIPELINE PICTURE
PR -> CI checks -> review -> merge -> build image (tag = commit) -> push to registry -> deploy to dev -> verify -> approve -> deploy same image to prod -> monitor -> rollback if needed.

WHY IT MATTERS
- Bugs caught minutes after writing, not weeks later in production.
- Repeatable, automated releases instead of manual 'deploy by hand' steps.
- Confidence to ship often.

REAL EXAMPLE
CI on every PR; merged images deployed to dev on our call; prod only with explicit per-step written approval and a rollback ready - continuous delivery, not continuous deployment, which suits an institutional client.
```

</details>

**Answer:** CI automatically builds and tests every change before merge; CD turns merged code into a release-ready artifact and deploys it repeatably — delivery needs an approval step, deployment is fully automatic. We ran continuous delivery: CI on every PR, dev deploys on merge, prod only with explicit approval and a rollback ready.

### 16. How does GitHub Actions work? Walk through a workflow file.

<details><summary>Understand it</summary>

```text
CONCEPTS
- Workflow: a YAML file in .github/workflows/ (e.g. ci.yml).
- Trigger ('on'): events like pull_request, push to main, schedule (cron), workflow_dispatch (manual button).
- Job: a set of steps running on one runner (a fresh VM, e.g. ubuntu-latest). Jobs run in parallel unless 'needs:' links them.
- Step: either 'uses:' (a reusable action, e.g. actions/checkout@v4) or 'run:' (a shell command).
- Matrix: run the same job across versions (Python 3.11 and 3.12).
- Secrets: ${{ secrets.NAME }} from repo/org settings; masked in logs.
- Artifacts and caching: save outputs; cache pip downloads to speed up.

EXAMPLE
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install -e ".[dev]"
      - run: ruff check . && mypy --strict src
      - run: pytest -q

RESULT
Each job shows a green tick or red cross on the PR. Branch protection can require them before merge.

GOTCHAS
- A scheduled workflow only runs from the default branch, and may never have run - check its history.
- Missing secrets make jobs red (we had a repo red because a private-package token secret was missing).
- Pin action versions.
```

</details>

**Answer:** A workflow is a YAML file in .github/workflows triggered by events like pull_request, push or a schedule. It has jobs running on fresh runners, each with steps that either use reusable actions like checkout or run shell commands — install, lint, type-check, test. Results show as checks on the PR, and branch protection can require them. Secrets come from repo settings, never the YAML.

### 17. What checks did your CI run, and why each?

<details><summary>Understand it</summary>

```text
THE GATES ON OUR AI PLATFORM
1. Ruff (lint/format): style, unused imports, common bugs. Also configured to BAN direct imports of LLM provider SDKs, enforcing the vendor-agnostic adapter.
2. mypy --strict (static types): catches None-used-as-number, wrong signatures, missing returns - Python otherwise only finds these at runtime.
3. pytest: unit and integration tests of logic.
4. Schemathesis (contract fuzzing): reads the API's OpenAPI schema, fires hundreds of generated requests (empty strings, huge values, odd Unicode, missing fields). Rule: may reject politely, must never return 500.
5. Hypothesis (property-based tests): you state a property ('forecast output length equals horizon'); it generates many inputs trying to break it.
6. Coverage jobs, and in AI systems ideally an eval harness: golden questions; fail if pass rate drops (e.g. below 90%).

HOW TO PRESENT IT
'Each gate catches a different class of bug: lint for style and banned imports, types for null bugs, tests for logic, contract fuzzing for API robustness, property tests for edge cases, evals for answer quality.'

DISCIPLINE
After every push, read the ACTUAL check results; explain every non-green check before asking for review.
```

</details>

**Answer:** Ruff for lint and to ban direct LLM SDK imports, mypy strict for type and None bugs, pytest for logic, Schemathesis to fuzz the API contract so it never returns a 500, Hypothesis for property-based edge cases, plus coverage — and for AI, an eval harness gate. Each catches a different class of bug, and I read the actual results after every push.

### 18. How do you handle secrets in CI/CD?

<details><summary>Understand it</summary>

```text
RULES
- Never in code or YAML. Store in GitHub Actions Secrets (repo/org/environment level) and reference as ${{ secrets.NAME }}.
- GitHub masks secret values in logs - but don't echo them anyway.
- Least privilege: tokens scoped to what the job needs (read-only package access, not admin).
- Environment protection: production secrets only available to jobs targeting the 'production' environment, which can require manual approval.
- Prefer short-lived credentials: OIDC federation (GitHub -> GCP/AWS) instead of long-lived cloud keys stored as secrets.
- Rotate regularly and after any exposure.
- Pull requests from forks don't get secrets by default (prevents theft via malicious PRs).

RUNTIME SECRETS (deployed app)
Env vars from a secrets manager (e.g. GCP Secret Manager) or a locked-down env file on the server; never baked into Docker images.

REAL EXAMPLE
A new repo's CI was red simply because the token secret needed to install private model packages hadn't been configured.
```

</details>

**Answer:** Secrets live in GitHub Actions secrets referenced by name, never in YAML; least-privilege tokens; production secrets gated behind an environment with approval; ideally OIDC short-lived cloud credentials instead of stored keys; rotate on exposure. At runtime secrets come from a secrets manager or locked-down env file, never the Docker image.

### 19. What is 'build once, deploy many'?

<details><summary>Understand it</summary>

```text
THE PRINCIPLE
Build the deployable artifact (Docker image) ONCE in CI, tag it uniquely (commit SHA), push it to a registry, and promote that identical artifact through dev -> staging -> prod. Only configuration (env vars) differs between environments.

WHY NOT REBUILD FOR PROD?
A rebuild can pull newer base images or library versions -> prod runs code you never tested. 'Works in dev' means nothing if prod is a different build.

HOW TO VERIFY IT'S THE SAME
Compare image digests (content hashes), not just tags (tags can be moved).

GOTCHA WE HIT
Prod ran a newer Docker (29, containerd image store) that reported the MANIFEST digest; dev's Docker 26 reported the CONFIG digest. Same image, different-looking IDs, so our deploy kit's ID check failed. Fix: compare the config digest on both sides.

ROLLBACK
Keep the previous image (and even the previous container, renamed) so rollback is one command.
```

</details>

**Answer:** Build the image once in CI, tag it with the commit, push it to a registry, and promote that exact image from dev to prod with only env config differing — a rebuild could pull untested versions. Verify by digest, not tag; we hit a case where newer Docker showed a manifest digest versus a config digest for the same image. Keep the previous image for rollback.


## Advanced Git

### 20. What are git worktrees and when are they useful?

<details><summary>Understand it</summary>

```text
WHAT THEY ARE
git worktree add ../wt-review pr-branch creates a second working folder linked to the same repository, with a different branch checked out. All worktrees share one .git history.

WHY USEFUL
- Review a teammate's PR or test a hotfix without stashing or disturbing your half-finished work.
- Run a long test suite on one branch while coding on another.
- Compare two versions side by side.

COMMANDS
git worktree add ../wt-fix fix/bug
git worktree list
git worktree remove ../wt-fix

VS CLONING AGAIN
Faster and saves disk; branches and commits are shared instantly.

REAL USE
On our platform I used dozens of worktrees (one per PR follow-up or review), so each review or fix had a clean, isolated folder.
```

</details>

**Answer:** Worktrees give a second working folder on another branch sharing the same repository, so I can review a PR or make a hotfix without stashing my current work. I used one per PR follow-up and review on our platform — dozens of them — which kept every change isolated.

### 21. What are tags, and how do you version releases?

<details><summary>Understand it</summary>

```text
TAGS
A tag is a permanent, named pointer to a specific commit (unlike branches, it doesn't move).
- Lightweight: git tag v1.2.0
- Annotated (recommended): git tag -a v1.2.0 -m "Release 1.2.0" - stores author, date, message.
- Push: git push origin v1.2.0 (tags aren't pushed by default).
- GitHub Releases build on tags (release notes, binaries).

SEMANTIC VERSIONING (MAJOR.MINOR.PATCH)
- MAJOR: breaking change (e.g. tool removed/renamed).
- MINOR: new feature, backward compatible.
- PATCH: bug fix.

AI CONTEXT
Model packages (wheels) versioned like models-mbs-w2d-tba 0.3.0. Pin exact versions in deployments so 'what model is running' is always known. Tag-triggered CI can build and publish packages/images.
```

</details>

**Answer:** A tag is a permanent pointer to a commit, ideally annotated, used for releases and GitHub Releases. I version with semantic versioning — major for breaking changes like a removed tool, minor for features, patch for fixes — and pin exact versions in deployments, like our model wheels at 0.3.0.

### 22. What are hooks and pre-commit?

<details><summary>Understand it</summary>

```text
GIT HOOKS
Scripts Git runs automatically at certain points: pre-commit (before a commit is created), commit-msg, pre-push, etc. Stored in .git/hooks (not shared by default).

PRE-COMMIT FRAMEWORK
A tool (pre-commit) with a shared config file (.pre-commit-config.yaml) in the repo, so the whole team runs the same checks before each commit:
- Formatters/linters (ruff, black)
- Secret scanners (gitleaks, detect-secrets)
- Trailing whitespace, large file checks, YAML validity

WHY
Catch problems seconds after writing, before CI. CI still re-runs everything (hooks can be skipped with --no-verify, which teams should not do).
```

</details>

**Answer:** Hooks run scripts at points like pre-commit or pre-push; the pre-commit framework shares one config so everyone runs the same formatters, linters and secret scanners before each commit. It catches issues in seconds, but CI still enforces them because hooks can be bypassed.

### 23. How do you keep a fork or a stale branch up to date, and what's cherry-pick?

<details><summary>Understand it</summary>

```text
KEEPING UP TO DATE
- Fork: add the original repo as 'upstream': git remote add upstream <url>; git fetch upstream; git rebase upstream/main (or merge).
- Stale branch: git fetch origin; git rebase origin/main; resolve conflicts; push --force-with-lease.

MULTIPLE REMOTES
A repo can push to several remotes (e.g. two GitHub accounts): git remote add backup <url>; git push backup main.

CHERRY-PICK
git cherry-pick <hash> copies ONE specific commit onto your current branch (new hash, same change).
Use cases: bring a hotfix from main into a release branch; rescue one commit from an abandoned branch.
Caution: duplicates commits; prefer merging when you need everything.
```

</details>

**Answer:** For a fork I add the original as upstream, fetch and rebase onto upstream main; for a stale branch I fetch, rebase onto origin main and force-with-lease. Cherry-pick copies one specific commit onto my branch, useful for moving a hotfix to a release branch.


## Docker basics

### 24. What is Docker and what problem does it solve?

<details><summary>Understand it</summary>

```text
THE PROBLEM
'It works on my machine.' Apps depend on a specific OS, Python version, system libraries and package versions. Your laptop and the server differ, so code that works locally breaks in production. AI apps are especially fragile (numpy, torch, CUDA, scikit-learn versions).

WHAT DOCKER DOES
Packages an application WITH everything it needs (code, runtime, libraries, OS files) into an IMAGE. That image runs as a CONTAINER identically on any machine with Docker - laptop, CI, dev server, prod.

BENEFITS
- Consistency across environments.
- Isolation: each service has its own dependencies; no conflicts.
- Fast start (seconds), lightweight (shares host kernel).
- Reproducible deploys and easy rollback (just run the previous image).
- Standard unit for orchestration (Compose, Kubernetes, Cloud Run).

ANALOGY
A shipping container: whatever is inside, ports and ships handle it the same way.
```

</details>

**Answer:** Docker packages an app with its code, runtime, libraries and OS files into an image that runs as an identical container anywhere, ending 'works on my machine'. It gives consistency, isolation, fast startup and easy rollback — on our AI platform every service, including the MCP model servers, ran as a container.

### 25. Image vs container?

<details><summary>Understand it</summary>

```text
IMAGE
- A read-only, layered snapshot: base OS files + runtime + libraries + your code + metadata (start command, env defaults, exposed ports).
- Built from a Dockerfile with docker build.
- Identified by a name:tag (mcp-mbs:main-1cdf749) and an immutable digest (sha256:...).
- Stored locally or in a registry.

CONTAINER
- A running (or stopped) instance of an image.
- Adds a thin writable layer on top; anything written there is lost when the container is removed.
- Has its own process space, network interface, filesystem view.
- Created with docker run (or docker create + start).

ANALOGY
Image = class / recipe. Container = object / dish. One image -> many containers.

KEY CONSEQUENCE
Containers are disposable: you don't patch them, you replace them with a new container from a new image. Persistent data goes in volumes or external databases.
```

</details>

**Answer:** An image is a read-only layered snapshot of code, runtime and libraries, built from a Dockerfile and identified by tag and digest; a container is a running instance of it with a thin writable layer. One image can run many containers, and containers are disposable — you replace them rather than patch them.

### 26. How is a container different from a virtual machine?

<details><summary>Understand it</summary>

```text
VIRTUAL MACHINE
- A hypervisor emulates hardware; each VM runs a FULL guest operating system with its own kernel.
- Gigabytes in size, boots in minutes, heavier on memory.
- Strong isolation (separate kernels).

CONTAINER
- Shares the HOST's kernel; isolation comes from Linux features: namespaces (separate view of processes, network, filesystem) and cgroups (CPU/memory limits).
- Megabytes, starts in seconds, many per host.
- Weaker isolation than VMs (shared kernel) - so run as non-root, keep images minimal.

IN PRACTICE THEY COMBINE
Our containers ran ON cloud VMs (Google Compute Engine): VMs for hardware isolation, containers for packaging and density.

ON WINDOWS/MAC
Docker Desktop runs a small Linux VM under the hood, because containers need a Linux kernel.
```

</details>

**Answer:** A VM virtualises hardware and runs a full guest OS, so it's gigabytes and slow to boot; a container shares the host kernel, isolated with namespaces and cgroups, so it's megabytes and starts in seconds. Isolation is weaker, so run as non-root. In practice they combine — our containers ran on cloud VMs.

### 27. Walk me through a Dockerfile for a Python AI service.

<details><summary>Understand it</summary>

```text
EXAMPLE
FROM python:3.12-slim                      # base image, pinned, small
WORKDIR /app                               # working directory inside image
COPY requirements.txt .                    # dependency list first (cache!)
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src                            # code last (changes most)
ENV PYTHONUNBUFFERED=1                     # logs appear immediately
EXPOSE 8000                                # documents the port
USER 1000                                  # don't run as root
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn","src.app:app","--host","0.0.0.0","--port","8000"]

INSTRUCTIONS EXPLAINED
- FROM: starting image.
- WORKDIR: cd for later instructions.
- COPY / ADD: files from build context into image (prefer COPY).
- RUN: execute a command at BUILD time, creating a layer.
- ENV: environment variable defaults (never secrets).
- EXPOSE: documentation; publishing needs -p at run.
- USER: which user runs the process.
- HEALTHCHECK: Docker marks container healthy/unhealthy.
- CMD: default command at RUN time (overridable). ENTRYPOINT: fixed executable; CMD then supplies default args.

BUILD
docker build -t myservice:1a2b3c4 .   ('.' = build context, filtered by .dockerignore)
```

</details>

**Answer:** FROM a pinned slim Python base, set WORKDIR, copy requirements and pip install first so that layer caches, then copy the source, set non-secret ENV defaults, EXPOSE the port, switch to a non-root USER, add a HEALTHCHECK, and CMD runs uvicorn. RUN executes at build time; CMD at container start.

### 28. What are layers and how does build caching work?

<details><summary>Understand it</summary>

```text
LAYERS
Each Dockerfile instruction that changes the filesystem (RUN, COPY, ADD) creates a layer - a diff on top of the previous one. An image is a stack of layers. Layers are shared between images (same base = stored once).

CACHING
When rebuilding, Docker reuses a cached layer if the instruction AND its inputs are unchanged. Once one layer changes, every layer after it is rebuilt.

WHY ORDER MATTERS
Bad:  COPY . .  then RUN pip install  -> any code edit invalidates the copy layer -> reinstall all libraries (minutes).
Good: COPY requirements.txt -> RUN pip install -> COPY src  -> code edits only rebuild the last layer (seconds).

OTHER TIPS
- Combine related RUN commands and clean up in the same layer (apt-get install ... && rm -rf /var/lib/apt/lists/*), because deleting in a later layer doesn't shrink earlier ones.
- .dockerignore keeps .git, data, caches out of the build context (faster, smaller, no secrets).
- Secrets copied into an early layer remain in the image even if deleted later - anyone can extract layers.
```

</details>

**Answer:** Each filesystem-changing instruction creates a cached layer; on rebuild Docker reuses layers until one changes, then rebuilds everything after. So I copy and install requirements before copying code, letting code edits rebuild in seconds. Clean up in the same RUN layer, use .dockerignore, and never copy secrets because deleted files remain in earlier layers.

### 29. How do you make images smaller and more secure?

<details><summary>Understand it</summary>

```text
SMALLER
- Slim or distroless base images (python:3.12-slim vs full python: hundreds of MB less).
- Multi-stage builds: stage 1 has compilers/build tools and builds wheels; stage 2 copies only the results into a clean slim image.
- --no-cache-dir for pip; clean apt lists in the same RUN.
- .dockerignore: exclude .git, data, notebooks, tests if not needed.

SECURER
- Run as non-root (USER).
- Pin base image versions (or digests); rebuild regularly for security patches.
- Scan images for vulnerabilities (Trivy, Docker Scout, registry scanning).
- No secrets in images (no COPY .env, no ENV API_KEY=...). Inject at runtime.
- Minimal packages = smaller attack surface.
- Read-only filesystem where possible; drop Linux capabilities.

MULTI-STAGE EXAMPLE
FROM python:3.12 AS build
RUN pip wheel -r requirements.txt -w /wheels
FROM python:3.12-slim
COPY --from=build /wheels /wheels
RUN pip install /wheels/*
```

</details>

**Answer:** Use slim bases, multi-stage builds so build tools stay out of the final image, no-cache installs and a .dockerignore. For security: non-root user, pinned and regularly rebuilt bases, vulnerability scanning, minimal packages, and never any secrets in the image — inject them at runtime.


## Docker commands & ops

### 30. What Docker commands do you use day to day?

<details><summary>Understand it</summary>

```text
BUILD & IMAGES
docker build -t name:tag .         build an image
docker images                      list images
docker pull / push name:tag        from/to a registry
docker tag src dst                 add another name
docker rmi image                   remove image

RUN & MANAGE CONTAINERS
docker run -d --name svc -p 8000:8000 --env-file prod.env name:tag
   -d background, -p host:container port, -v volume, --rm remove on exit, --restart unless-stopped
docker ps / docker ps -a           running / all containers
docker logs -f svc                 follow logs
docker exec -it svc bash           shell inside a running container
docker stop svc / start / restart
docker rm svc                      remove container
docker inspect svc                 full JSON: env, mounts, image ID, health
docker stats                       live CPU/memory
docker cp file svc:/path           copy files in/out

CLEANUP
docker system df / docker system prune

COMPOSE
docker compose up -d / down / ps / logs -f / pull
```

</details>

**Answer:** build and tag images, run with -d, -p, --env-file and a name, ps to list, logs -f to follow, exec -it for a shell, inspect for env and image ID, stats for resources, stop and rm to remove, pull and push for registries, system prune to clean up, and the docker compose equivalents for multi-service stacks.

### 31. How do containers persist data? Volumes vs bind mounts.

<details><summary>Understand it</summary>

```text
THE PROBLEM
A container's writable layer disappears when the container is removed. Databases, uploads, model caches must survive.

VOLUMES (Docker-managed)
docker run -v pgdata:/var/lib/postgresql/data postgres
- Stored in Docker's area on the host; managed with docker volume ls/rm.
- Best for persistent app data; portable across containers.

BIND MOUNTS (host folder)
docker run -v /home/me/project:/app ...
- Maps an exact host path into the container.
- Great in development (edit code on host, see it in container instantly), config files.
- Ties the container to the host's filesystem layout.

tmpfs: in-memory, for temporary sensitive data.

PRODUCTION PRACTICE
Often the database is a MANAGED service outside Docker (our case: Cloud SQL with daily backups), so app containers stay stateless and can be replaced freely. Gotcha: /tmp on some hosts is tmpfs (wiped on reboot) - keep deploy kits/backups elsewhere.
```

</details>

**Answer:** Data written inside a container dies with it, so I use named volumes for persistent data and bind mounts for development code or config files. In production I prefer stateless containers with a managed database outside Docker — ours was Cloud SQL with daily backups — so containers can be replaced freely.

### 32. How do containers communicate? Ports and networks.

<details><summary>Understand it</summary>

```text
PORTS
-p 8000:8000 publishes container port 8000 on host port 8000 so outside clients can reach it. Without -p, the service is only reachable inside Docker networks. -p 127.0.0.1:8000:8000 binds to localhost only (not exposed publicly).

NETWORKS
- Default bridge network: containers get internal IPs.
- User-defined networks (and every Compose project): containers reach each other BY NAME via built-in DNS: http://mcp:8000.
- docker network create appnet; docker run --network appnet --name mcp ...

TYPICAL LAYOUT
Only Nginx publishes 443/80 to the internet; chat, MCP servers and gateways sit on an internal network, unreachable directly from outside.

DEBUGGING
docker exec -it chat curl http://mcp:8000/health ; docker network inspect appnet.
```

</details>

**Answer:** -p publishes a container port on the host; without it a service is only reachable on Docker networks. On a user-defined or Compose network containers reach each other by name through built-in DNS. I publish only the reverse proxy to the internet and keep app services internal, binding to localhost where needed.

### 33. What is Docker Compose and when do you use it?

<details><summary>Understand it</summary>

```text
WHAT IT IS
A tool to define and run multi-container applications from one YAML file (docker-compose.yml / compose.yaml).

EXAMPLE
services:
  chat:
    image: chat:main-1a2b3c4
    ports: ["8000:8000"]
    env_file: prod.env
    depends_on: [mcp]
  mcp:
    image: mcp-mbs:main-1cdf749
    restart: unless-stopped
    healthcheck: {test: ["CMD","curl","-f","http://localhost:8000/health"]}
  nginx:
    image: nginx:1.27
    ports: ["443:443"]
    volumes: ["./nginx.conf:/etc/nginx/nginx.conf:ro"]

COMMANDS
docker compose up -d | down | ps | logs -f chat | pull | up -d --force-recreate chat

FEATURES
Shared network with name-based DNS, volumes, env files, restart policies, healthchecks, depends_on (start order; with condition: service_healthy to wait for health).

WHEN
Local development of multi-service apps, single-host deployments, CI integration tests. For many hosts / autoscaling -> Kubernetes or managed services.
```

</details>

**Answer:** Compose defines a multi-container app in one YAML — services, images, ports, env files, volumes, healthchecks, restart policies and dependencies — on a shared network where services find each other by name. I use it for local multi-service development, CI integration tests and single-host deployments; Kubernetes when I need many hosts.

### 34. How do you pass configuration and secrets to containers?

<details><summary>Understand it</summary>

```text
CONFIGURATION
Twelve-factor principle: config in the environment, not in the code or image. Same image for dev and prod; only env differs.
- docker run -e LOG_LEVEL=INFO ...
- docker run --env-file prod.env ...
- Compose: environment: / env_file:

SECRETS
- Never in the Dockerfile (ENV/COPY) - layers are extractable.
- Runtime injection: env file with tight permissions on the server, Docker/Compose secrets (mounted files), or fetched from a secrets manager (GCP Secret Manager, Vault) at start.
- Don't log them; don't print env vars by name pattern (DATABASE_URL contains the password).

THE TRAP (real)
Env vars are fixed when a container is CREATED. docker restart reuses them - it does NOT re-read an edited env file. We rotated a JWT secret and swapped a model setting, restarted, and both fixes silently never took effect for hours. Correct: docker stop && docker rm && docker run --env-file ... (or docker compose up -d --force-recreate). Then VERIFY: docker inspect / an endpoint that reports the active config.

ALSO
docker cp + restart works for patching source files (Python re-reads files on import) but is a fragile hot-patch - prefer building a proper image.
```

</details>

**Answer:** Config comes from environment variables or an env file at run time, so one image serves dev and prod; secrets are injected at runtime from a locked-down file or a secrets manager, never baked into the image or logged. The trap: env vars are fixed at container creation, so docker restart doesn't pick up an edited env file — you must recreate the container and verify, which bit us during a key rotation.

### 35. A container keeps crashing. How do you debug it?

<details><summary>Understand it</summary>

```text
STEP BY STEP
1. docker ps -a - status and exit code (Exited (1), (137) = killed, often out of memory, (139) = segfault).
2. docker logs <name> (and --tail 100) - the actual error: import error, missing env var, port in use, DB unreachable.
3. docker inspect <name> - env vars actually set, mounts, restart count, OOMKilled flag, health status, image ID.
4. Reproduce interactively: docker run -it --entrypoint bash image - then run the start command by hand.
5. If it starts then dies: docker exec -it <name> bash quickly, or check healthcheck failures.
6. docker stats - memory/CPU pressure.
7. Common causes:
   - Missing/wrong env var or secret
   - Can't reach database (network, TLS, firewall)
   - App binds to 127.0.0.1 instead of 0.0.0.0 inside container (unreachable)
   - Port already used on host
   - Out of memory (big models!)
   - Wrong architecture (arm64 image on amd64)
   - File permissions when running as non-root
8. Fix -> rebuild/recreate -> verify functionally (health endpoint, real request).
```

</details>

**Answer:** Check docker ps -a for the exit code, read docker logs, then docker inspect for the env actually set, mounts, OOMKilled and health. Reproduce by running the image with a bash entrypoint and starting the app by hand. Usual causes: missing env vars, database unreachable, binding to 127.0.0.1 instead of 0.0.0.0, port clashes, out of memory or permissions. Then recreate and verify functionally.


## Deploying with Docker

### 36. How do you deploy a new version with zero or minimal downtime and roll back?

<details><summary>Understand it</summary>

```text
SINGLE-HOST APPROACH (what we did)
1. CI built the image tagged by commit; pull it on the server.
2. Verify the image ID/digest matches what was tested on dev.
3. Rename the old container and keep it (e.g. mcp-mbs-pre-rollout-<timestamp>) - instant rollback.
4. Start the new container with the same config.
5. Health check + functional verification: all tools respond (gateway 16/16 tools), real answers correct.
6. Record what is live (image, time, verifier). Downtime ~3.4 minutes.
7. Rollback script ready: stop new, start old.

FOR TRUE ZERO DOWNTIME
- Blue-green: run new version alongside old, switch the proxy (Nginx upstream) when healthy, keep old for rollback.
- Rolling updates: replace instances one by one behind a load balancer (Kubernetes/Cloud Run do this automatically).
- Canary: send a small % of traffic to the new version first.
Requires: health checks, backward-compatible DB changes, stateless services.

PROCESS
Dev first; prod only with explicit approval, during a low-usage window, avoiding scheduled jobs (e.g. a 06:17 UTC pipeline cron).
```

</details>

**Answer:** Pull the commit-tagged image, verify its digest matches dev, keep the old container renamed for instant rollback, start the new one, then health-check and verify functionally before recording what's live — our prod swap took about three minutes with all 16 tools verified. For zero downtime: blue-green behind Nginx, rolling or canary deploys with health checks.

### 37. What is a container registry and why use one?

<details><summary>Understand it</summary>

```text
WHAT IT IS
A server that stores and distributes Docker images (and often other artifacts). You push images from CI and pull them on servers.
Examples: Docker Hub, GitHub Container Registry (ghcr.io), Google Artifact Registry, AWS ECR.

WHY
- Single source of truth for built images; build once in CI, pull anywhere.
- Access control (private images), vulnerability scanning, retention policies.
- Immutable digests; tags for humans.

TAGGING STRATEGY
- Unique, immutable tags: commit SHA (main-1cdf749) or version (1.4.2).
- Avoid deploying 'latest' - you can't tell what's running and it can change under you.

ALSO FOR PYTHON PACKAGES
Artifact Registry can host private Python package indexes too - I proposed it for our model wheels and images (GCP-native, IAM-controlled).
```

</details>

**Answer:** A registry stores and serves images — Docker Hub, GHCR, Google Artifact Registry — so CI builds once and servers pull the exact image with access control and scanning. Tag with immutable commit SHAs or versions, never deploy latest. I proposed Artifact Registry for both our images and our private model wheels.

### 38. Docker vs Kubernetes — when do you need Kubernetes?

<details><summary>Understand it</summary>

```text
DOCKER (+ COMPOSE)
Builds and runs containers on ONE host. Simple, easy to debug. Great for dev, CI, small single-server deployments.

KUBERNETES
An orchestrator for containers across MANY machines:
- Scheduling containers onto nodes
- Self-healing (restart/replace failed pods)
- Autoscaling (more replicas under load)
- Rolling updates and rollbacks
- Service discovery and load balancing
- Config and secrets objects
Cost: significant operational complexity (clusters, manifests/Helm, networking, RBAC).

WHEN TO MOVE
Many services, many hosts, autoscaling needs, high availability requirements, a team able to operate it - or use a managed option (GKE, EKS) or simpler serverless containers (Cloud Run).

OUR CHOICE
Docker on Compute Engine VMs: right-sized for a handful of services and one main client. Growth path: Cloud Run for stateless services, GKE when scale demands.
```

</details>

**Answer:** Docker and Compose run containers on one host — simple and debuggable. Kubernetes orchestrates across many machines with scheduling, self-healing, autoscaling, rolling updates and service discovery, at real operational cost. I'd move to Kubernetes or Cloud Run when services, hosts and availability needs grow; for our scale, Docker on VMs was right-sized.

### 39. How does Docker fit into your CI/CD pipeline end to end?

<details><summary>Understand it</summary>

```text
THE FULL PICTURE
1. Developer pushes a branch, opens a PR.
2. GitHub Actions: lint, types, tests, contract fuzzing (often running the service in a container), eval harness.
3. Review and merge to main.
4. CI builds the Docker image ONCE, tags with the commit SHA, (scans it), pushes to the registry.
5. Deploy to dev: pull the image, recreate the container with dev env file, run health + functional checks.
6. Approval for prod (explicit, per step).
7. Deploy SAME image to prod with prod env file; keep previous container for rollback; verify.
8. Monitor: logs, metrics (Grafana), health tools, data freshness alerts.
9. Rollback = run previous image.

WHAT THIS GIVES YOU
Traceability (commit -> image -> running container), repeatability, fast rollback, and confidence that prod runs exactly what was tested.
```

</details>

**Answer:** PR triggers CI checks, review and merge; CI builds one image tagged by commit and pushes it to a registry; dev pulls and recreates the container with dev config and verifies; with explicit approval prod runs the same image with prod config, keeping the old container for rollback; then monitoring. That gives traceability from commit to running container and one-command rollback.

### 40. What is the difference between CMD and ENTRYPOINT, and RUN?

<details><summary>Understand it</summary>

```text
RUN
Executes at BUILD time; result saved in a layer. e.g. RUN pip install -r requirements.txt.

CMD
Default command (or default args) executed when the CONTAINER STARTS. Overridden by arguments to docker run: docker run image python other.py replaces CMD.

ENTRYPOINT
The fixed executable that always runs at start. Arguments to docker run are appended to it. CMD then supplies default arguments.
ENTRYPOINT ["python","-m","mytool"]
CMD ["--help"]
docker run image --version  -> python -m mytool --version

EXEC FORM vs SHELL FORM
Prefer JSON array (exec) form: CMD ["uvicorn","app:app"] - the process gets PID 1 and receives stop signals properly (graceful shutdown). Shell form (CMD uvicorn app:app) wraps in /bin/sh, which may not forward signals.
```

</details>

**Answer:** RUN executes at build time and creates a layer; CMD is the default start command or arguments, overridden by docker run arguments; ENTRYPOINT is the fixed executable with CMD as default args. Use exec JSON form so the app is PID 1 and shuts down gracefully on stop signals.

