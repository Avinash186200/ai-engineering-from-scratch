# Cheat sheet: Git, GitHub, Docker, Compose

Every command from Day 11, grouped. Practise them in the labs: [git/LAB.md](git/LAB.md), [docker/LAB.md](docker/LAB.md).


## Git

| Area | Command | What it does | Note |
|---|---|---|---|
| Setup | `git config --global user.name / user.email` | Set your identity for commits | Once per machine |
| Start | `git clone <url>` | Copy a repo with full history | git clone https://github.com/org/repo.git |
| Start | `git init` | Turn a folder into a new repo |  |
| Inspect | `git status` | What changed, what's staged | Type it constantly |
| Inspect | `git diff / git diff --staged` | Line changes unstaged / staged |  |
| Inspect | `git log --oneline --graph -10` | Recent history as a graph |  |
| Inspect | `git show <hash>` | What one commit changed | git show 1cdf749 |
| Inspect | `git blame <file>` | Who last changed each line |  |
| Save | `git add <file> / git add -p` | Stage a file / stage chosen hunks | -p = pick pieces interactively |
| Save | `git commit -m "msg"` | Save staged snapshot | Imperative message: what + why |
| Save | `git commit --amend` | Fix last commit (unpushed) |  |
| Branch | `git switch -c <branch>` | Create and switch to branch | git switch -c fix/typed-errors |
| Branch | `git switch <branch>` | Switch branch |  |
| Branch | `git branch / git branch -d <b>` | List / delete merged branch |  |
| Remote | `git remote -v / git remote add <name> <url>` | List / add remotes | Push to two remotes |
| Remote | `git fetch origin` | Download remote changes, don't touch your branch | Then diff vs origin/main |
| Remote | `git pull` | Fetch + merge (or rebase) into current branch | git config pull.rebase true |
| Remote | `git push -u origin <branch>` | Publish branch, set upstream |  |
| Remote | `git push --force-with-lease` | Safe force push after rebase | Refuses if others pushed |
| Integrate | `git merge <branch>` | Join histories with merge commit | Safe on shared branches |
| Integrate | `git rebase origin/main` | Replay your commits on latest main | Private branches only |
| Integrate | `git cherry-pick <hash>` | Copy one commit here | Hotfix to release branch |
| Undo | `git restore <file>` | Discard working edits | Irreversible for those edits |
| Undo | `git restore --staged <file>` | Unstage |  |
| Undo | `git reset --soft\|--mixed\|--hard <hash>` | Move branch back (local) | --hard destroys work |
| Undo | `git revert <hash>` | New commit undoing a pushed one | Safe for shared history |
| Undo | `git stash / git stash pop` | Park and restore work |  |
| Undo | `git reflog` | Every past HEAD position: recover lost commits |  |
| Debug | `git bisect start / bad / good <hash>` | Binary search for a bad commit | git bisect run ./test.sh |
| Pro | `git worktree add ../wt <branch>` | Second folder on another branch | Review PRs without stashing |
| Pro | `git tag -a v1.2.0 -m msg ; git push origin v1.2.0` | Mark a release |  |

## GitHub

| Area | Command | What it does | Note |
|---|---|---|---|
| CLI | `gh pr create --fill` | Open a PR from current branch |  |
| CLI | `gh pr checks <n>` | See real CI results | Read after every push |
| CLI | `gh pr view <n> --comments` | Read PR conversation | Also check inline + review bodies |
| CLI | `gh pr diff <n> / gh pr checkout <n>` | See / check out a PR |  |
| Actions | `.github/workflows/ci.yml` | CI workflow file | on: pull_request -> jobs -> steps |
| Actions | `${{ secrets.NAME }}` | Use a stored secret | Never paste keys in YAML |

## Docker

| Area | Command | What it does | Note |
|---|---|---|---|
| Build | `docker build -t name:tag .` | Build image from Dockerfile | Tag with commit SHA |
| Images | `docker images / docker rmi <img>` | List / remove images |  |
| Registry | `docker pull / push name:tag` | Download / upload image | Artifact Registry, GHCR, Docker Hub |
| Run | `docker run -d --name svc -p 8000:8000 --env-file prod.env img:tag` | Start container | -d bg, -p ports, -v volumes, --rm |
| Inspect | `docker ps / docker ps -a` | Running / all containers | Exit codes: 137 = killed (OOM) |
| Inspect | `docker logs -f --tail 100 svc` | Follow container logs |  |
| Inspect | `docker exec -it svc bash` | Shell inside running container |  |
| Inspect | `docker inspect svc` | Env, mounts, image ID, health | Verify config is really live |
| Inspect | `docker stats` | Live CPU/memory |  |
| Manage | `docker stop / start / restart svc` | Lifecycle | restart does NOT re-read env file |
| Manage | `docker rm svc ; docker run ... (recreate)` | Pick up new env/config | Or compose up -d --force-recreate |
| Manage | `docker rename svc svc-old` | Keep old container for rollback |  |
| Manage | `docker cp file svc:/path` | Copy files in/out | Hot-patch only; prefer rebuild |
| Data | `docker volume ls / -v vol:/path` | Named volumes |  |
| Network | `docker network create net ; --network net` | Name-based container DNS |  |
| Clean | `docker system df / docker system prune` | Disk usage / cleanup |  |

## Compose

| Area | Command | What it does | Note |
|---|---|---|---|
| Run | `docker compose up -d / down` | Start / stop whole stack |  |
| Inspect | `docker compose ps / logs -f <svc>` | Status / logs |  |
| Update | `docker compose pull && docker compose up -d` | Deploy new images |  |
