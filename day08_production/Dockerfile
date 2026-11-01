# Build from the repo root:  docker build -f day08_production/Dockerfile -t fund-assistant .
# Run:                       docker run -p 8000:8000 fund-assistant
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir pandas numpy scikit-learn langgraph pydantic fastapi uvicorn anthropic
# Copy only the files the service needs, never the whole folder (no .env, no notebooks).
COPY core/__init__.py core/fund_model.py core/llm.py core/
COPY data/__init__.py data/make_data.py data/funds.csv data/
COPY day03_agents/agent.py day03_agents/
COPY day08_production/app.py day08_production/llm_adapter.py day08_production/
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "app:app", "--app-dir", "day08_production", "--host", "0.0.0.0", "--port", "8000"]
