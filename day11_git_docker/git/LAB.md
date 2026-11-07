# Git hands-on lab (Day 11, Part 1)

Practise in a throwaway folder, so nothing here can hurt a real project.
Each step: what to type, what you should see, what it teaches.

## 0. One-time setup

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
git config --global pull.rebase true        # optional: linear history on pull
```

## 1. The four boxes

```bash
mkdir git-lab && cd git-lab && git init
echo "TIMEOUT_SECONDS = 30" > server.py
git status                 # server.py is untracked (working folder)
git add server.py
git status                 # now staged
git commit -m "Add server timeout setting"
git log --oneline          # one commit in local history
```
**Teaches:** working folder -> `git add` -> staging -> `git commit` -> local history. `git push` is the fourth box (GitHub).

## 2. Look at changes

```bash
echo "RETRIES = 3" >> server.py
git diff                   # unstaged change
git add server.py
git diff --staged          # staged change
git commit -m "Add retry count"
git show HEAD              # what the last commit changed
git blame server.py        # who changed each line
```

## 3. A branch and a merge conflict

```bash
git switch -c fix/slow-models
sed -i 's/30/60/' server.py           # (on Mac: sed -i '' 's/30/60/' server.py)
git commit -am "Raise timeout for slow models"

git switch main
sed -i 's/30/45/' server.py
git commit -am "Raise timeout slightly"

git merge fix/slow-models             # CONFLICT
git status                            # server.py: both modified
```
Open `server.py`. You'll see `<<<<<<<`, `=======`, `>>>>>>>`. Decide the right value (say 60), delete the markers, then:
```bash
git add server.py
git commit                            # completes the merge
git log --oneline --graph --all
```
**Teaches:** a conflict = two branches changed the same lines. You decide, remove the markers, add, commit.
`git merge --abort` gets you out if you panic.

## 4. Rebase instead of merge

```bash
git switch -c feat/logging main~1     # branch from an older commit
echo "LOG_LEVEL = 'INFO'" > logging_cfg.py
git add . && git commit -m "Add log level"
git rebase main                       # replay your commit on top of latest main
git log --oneline --graph --all       # straight line
```
**Teaches:** rebase rewrites your commits (new hashes). Fine on your own branch; never on a branch others use.

## 5. Undo, safely

```bash
echo "oops" >> server.py
git restore server.py                 # discard the edit

echo "BAD = True" >> server.py && git commit -am "Bad change"
git revert HEAD                       # new commit that undoes it: safe for shared history

git reset --soft HEAD~1               # undo the revert commit, keep its changes staged (local only)
git reset --hard HEAD                 # throw those staged changes away (destructive)
git reflog                            # every place HEAD has been: your safety net
```

## 6. Stash and worktrees

```bash
echo "half finished" >> server.py
git stash                             # park it
git switch main && git switch -       # move around freely
git stash pop                         # bring it back

git worktree add ../git-lab-review fix/slow-models   # second folder, other branch
git worktree list
git worktree remove ../git-lab-review
```
**Teaches:** worktrees let you review a PR or hotfix without disturbing your own half-finished work.

## 7. Find the commit that broke something (bisect)

```bash
for i in 1 2 3 4 5 6; do echo "step $i" >> steps.txt; git add steps.txt; git commit -qm "Step $i"; done
echo "BROKEN" >> steps.txt && git commit -qam "Step 7 (introduces bug)"
for i in 8 9; do echo "step $i" >> steps.txt; git commit -qam "Step $i"; done

git bisect start
git bisect bad                        # now is broken
git bisect good HEAD~9                # this old one was fine
git bisect run sh -c '! grep -q BROKEN steps.txt'   # automatic: exit 0 = good
git bisect reset
```
**Teaches:** binary search through history; about 10 tests for 1,000 commits.

## 8. GitHub: branch, push, pull request

In a repo you own on GitHub (or a fork):
```bash
git switch main && git pull
git switch -c docs/readme-typo
# edit README.md
git commit -am "Fix typo in README"
git push -u origin docs/readme-typo
gh pr create --fill                   # or open the PR on github.com
gh pr checks                          # read the real CI results
```
Then: review the diff yourself, make sure every check is green, merge on GitHub, and back locally:
```bash
git switch main && git pull && git branch -d docs/readme-typo
```

## 9. Tag a release

```bash
git tag -a v1.0.0 -m "First release"
git push origin v1.0.0
```

## 10. Never commit a secret

```bash
echo "API_KEY=abc" > .env
echo ".env" >> .gitignore
git status                            # .env does not appear
```
If a secret ever does get pushed: **rotate the key first**, then clean history (git filter-repo / BFG). Deleting
the file in a new commit does not remove it from history.
