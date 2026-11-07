# Day 11: Git, GitHub, CI/CD and Docker

How real AI teams track, review, test, package and ship code.

| | Video | Short |
|---|---|---|
| Part 1: Git and GitHub | [watch](https://youtu.be/9UtT53lkoxo) | [Git in 60 seconds](https://youtube.com/shorts/wDmf1VPZ3UI) |
| Part 2: Docker | [watch](https://youtu.be/i3KMQ2z-cVc) | [Docker in 60 seconds](https://youtube.com/shorts/y9hwbf-fuL4) |

## What's here

| File | What it is |
|---|---|
| [git/LAB.md](git/LAB.md) | Hands-on Git lab: the four boxes, branches, a real merge conflict, rebase, undo, stash, worktrees, bisect, pull requests, tags |
| [git/ci_example.yml](git/ci_example.yml) | A GitHub Actions workflow: lint, types, tests, then build an image tagged with the commit |
| [docker/app.py](docker/app.py) | A tiny model service (FastAPI) with `/health`, `/config`, `/forecast` |
| [docker/Dockerfile](docker/Dockerfile) | Pinned slim base, libraries before code (layer caching), non-root user, healthcheck |
| [docker/docker-compose.yml](docker/docker-compose.yml) + [nginx.conf](docker/nginx.conf) | Two services: the model behind Nginx, reached by service name |
| [docker/dev.env](docker/dev.env), [prod.env.example](docker/prod.env.example) | Config via env files (real `prod.env` is gitignored) |
| [docker/LAB.md](docker/LAB.md) | Hands-on Docker lab, including the `docker restart` env trap and a deploy with rollback |
| [CHEATSHEET.md](CHEATSHEET.md) | Every command, grouped |
| [INTERVIEW_QA.md](INTERVIEW_QA.md) | 40 interview questions, each with a full explanation and a spoken answer |

## Quick start

```bash
python day11_git_docker/docker/app.py --selftest                       # no Docker needed
docker build -f day11_git_docker/docker/Dockerfile -t day11-model:local .
docker run -d --name day11 -p 8000:8000 --env-file day11_git_docker/docker/dev.env day11-model:local
curl http://localhost:8000/config
```

## Five lessons from a real production AI platform

1. A branch made from an old commit silently missed 19 later merges. Always `git fetch` and diff against `origin/main`.
2. A whole repo's CI was red because a token secret had not been added. Secrets live in GitHub Secrets; read the actual check results after every push.
3. `docker restart` does not re-read an edited env file. A rotated key stayed un-applied for hours. Recreate the container, then verify.
4. Two Docker versions reported different-looking IDs (manifest vs config digest) for the same image. Know what an ID refers to before a safety check trusts it.
5. A production swap kept the old container, renamed, for a one-command rollback: about 3 minutes of downtime, every tool verified before calling it done.
