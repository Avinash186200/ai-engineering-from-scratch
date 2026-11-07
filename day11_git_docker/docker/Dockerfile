# Day 11 model service.
# Build from the REPO ROOT:  docker build -f day11_git_docker/docker/Dockerfile -t day11-model:local .
# Run:                       docker run -d --name day11 -p 8000:8000 --env-file day11_git_docker/docker/dev.env day11-model:local

# 1. Pinned, slim base image (never python:latest)
FROM python:3.11-slim

# Logs appear immediately; no .pyc files in the image
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 2. Libraries first: this layer is cached until requirements change
COPY day11_git_docker/docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Code last: editing code only rebuilds from here (seconds, not minutes)
COPY day11_git_docker/__init__.py day11_git_docker/
COPY day11_git_docker/docker/__init__.py day11_git_docker/docker/app.py day11_git_docker/docker/

# 4. Never run as root
RUN useradd --create-home app
USER app

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Exec (JSON) form: the server is PID 1 and receives stop signals properly
CMD ["uvicorn", "day11_git_docker.docker.app:app", "--host", "0.0.0.0", "--port", "8000"]
