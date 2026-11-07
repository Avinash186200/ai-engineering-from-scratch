# Docker hands-on lab (Day 11, Part 2)

Run every command from the **repo root**. You need Docker Desktop (Windows/Mac) or Docker Engine (Linux).
Each step says what to type, what you should see, and what it teaches.

## 0. Check the app works without Docker

```bash
python day11_git_docker/docker/app.py --selftest
```
You should see `day11 docker app selftest: OK`.

## 1. Build an image

```bash
docker build -f day11_git_docker/docker/Dockerfile -t day11-model:local .
docker images day11-model
```
**Teaches:** an image is a packaged snapshot: Python, libraries, code. The `.` is the *build context*
(the repo root); the root `.dockerignore` keeps `.git`, caches and `*.env` files out of it.

## 2. See layer caching

Edit a comment in `app.py`, then build again. Watch the output: the `pip install` step says `CACHED`
and only the code-copy steps rerun.
**Teaches:** libraries first, code last, so code edits rebuild in seconds.

## 3. Run a container

```bash
docker run -d --name day11 -p 8000:8000 --env-file day11_git_docker/docker/dev.env day11-model:local
docker ps
curl http://localhost:8000/health
curl http://localhost:8000/config
curl "http://localhost:8000/forecast?horizon=21"
```
**Teaches:** `-d` runs in the background, `-p host:container` publishes the port, `--env-file`
supplies configuration. `/config` shows `"model": "fake-model"`, and `api_key_set: true`, but never the key itself.

## 4. Look inside

```bash
docker logs -f day11          # Ctrl+C to stop following
docker exec -it day11 bash    # a shell inside the container; type exit to leave
docker inspect day11 --format '{{json .Config.Env}}'
docker stats --no-stream
```

## 5. The restart trap (this bit a real production system)

1. Edit `day11_git_docker/docker/dev.env`: change `MODEL_NAME=fake-model` to `MODEL_NAME=better-model`.
2. Restart and check:
   ```bash
   docker restart day11
   curl http://localhost:8000/config
   ```
   It still says **fake-model**. `docker restart` reuses the environment the container was **created** with.
3. Recreate it, then verify:
   ```bash
   docker stop day11 && docker rm day11
   docker run -d --name day11 -p 8000:8000 --env-file day11_git_docker/docker/dev.env day11-model:local
   curl http://localhost:8000/config
   ```
   Now it says **better-model**.

**Teaches:** env vars are fixed at container creation. After any config or secret change: recreate, then
*verify the new value is live* (an endpoint like `/config`, or `docker inspect`). Set `dev.env` back afterwards.

## 6. Deploy with a rollback (the production pattern)

```bash
docker build -f day11_git_docker/docker/Dockerfile -t day11-model:v2 .   # in real life: tag = commit SHA
docker rename day11 day11-old && docker stop day11-old                   # keep the old one
docker run -d --name day11 -p 8000:8000 --env-file day11_git_docker/docker/dev.env day11-model:v2
curl http://localhost:8000/health                                        # verify before you call it done
# Rollback, if needed:
#   docker stop day11 && docker rm day11 && docker rename day11-old day11 && docker start day11
docker rm day11-old    # only once you're sure
```

## 7. Two services with Compose

```bash
docker stop day11 && docker rm day11
docker compose -f day11_git_docker/docker/docker-compose.yml up -d --build
docker compose -f day11_git_docker/docker/docker-compose.yml ps
curl http://localhost:8080/config     # through Nginx; the model has no published port
docker compose -f day11_git_docker/docker/docker-compose.yml logs -f model
docker compose -f day11_git_docker/docker/docker-compose.yml down
```
**Teaches:** services reach each other by name (`http://model:8000` in `nginx.conf`); only the front door
publishes a port. To pick up env changes in Compose: `up -d --force-recreate`.

## 8. Clean up

```bash
docker system df
docker image rm day11-model:local day11-model:v2
docker system prune     # removes stopped containers, unused networks, dangling images
```

## Debugging a crashing container: checklist

1. `docker ps -a`: exit code (`137` = killed, often out of memory).
2. `docker logs <name>`: the actual error.
3. `docker inspect <name>`: env actually set, mounts, `OOMKilled`, health.
4. `docker run -it --entrypoint bash <image>`, then start the app by hand.
5. Usual causes: missing env var, can't reach the database, app bound to `127.0.0.1` instead of `0.0.0.0`,
   port already in use, out of memory, file permissions as a non-root user.
