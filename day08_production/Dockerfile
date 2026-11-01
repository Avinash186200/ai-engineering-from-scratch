# Build from the repo root:  docker build -f day08_production/Dockerfile -t chatbot .
# Run:                       docker run --env-file prod.env -p 8000:8000 chatbot
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ core/
COPY day08_production/ day08_production/
# The service also runs the Day 3 agent, its system prompt, and the synthetic data.
COPY data/ data/
COPY day02_prompting/system_prompt.md day02_prompting/
COPY day03_agents/ day03_agents/
RUN python data/make_data.py

RUN useradd --create-home app
USER app

EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"
CMD ["uvicorn", "day08_production.app:app", "--host", "0.0.0.0", "--port", "8000"]
