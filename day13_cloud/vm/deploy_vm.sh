#!/usr/bin/env bash
# Swap a container on a single VM with a one-command rollback.
# The pattern used for a real production model server: pull, verify the image, keep the old
# container (renamed, stopped), start the new one, smoke test, roll back automatically on failure.
#
# Usage:  ./deploy_vm.sh asia-south1-docker.pkg.dev/my-proj/apps/model-service main-ce57d87
set -euo pipefail

IMAGE="$1"; TAG="$2"
NAME=model-service
ENV_FILE=/etc/model-service/prod.env      # root-owned, chmod 600; never in Git or the image
PORT=8000

echo "1. Pull the exact image CI built and dev verified"
docker pull "$IMAGE:$TAG"
docker image inspect "$IMAGE:$TAG" --format 'image id: {{.Id}}'
# Compare this ID with what dev ran. Note: different Docker versions can show a different
# kind of digest for the same image; compare like with like.

echo "2. Keep the old container for rollback"
if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
  docker rm -f "${NAME}-previous" 2>/dev/null || true
  docker stop "$NAME"
  docker rename "$NAME" "${NAME}-previous"
fi

echo "3. Start the new container (a NEW container, so it reads the env file fresh)"
docker run -d --name "$NAME" --restart unless-stopped \
  -p 127.0.0.1:$PORT:8000 --env-file "$ENV_FILE" -e APP_VERSION="$TAG" \
  "$IMAGE:$TAG"

echo "4. Wait for health, then smoke test"
for i in $(seq 1 30); do
  curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break
  sleep 2
done

# smoke_test.py (from this folder) is copied next to this script; it needs only the standard library.
if python3 smoke_test.py "http://127.0.0.1:$PORT" --version "$TAG"; then
  echo "5. Live: $IMAGE:$TAG. Old container kept as ${NAME}-previous (stopped)."
else
  echo "Smoke test failed: rolling back"
  docker rm -f "$NAME"
  docker rename "${NAME}-previous" "$NAME"
  docker start "$NAME"
  exit 1
fi

# Manual rollback later:
#   docker rm -f model-service && docker rename model-service-previous model-service && docker start model-service
