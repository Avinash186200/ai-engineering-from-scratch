"""A tiny 'model service' to practise Docker with (Day 11, Part 2).

It reports which model it is configured to use and a version, both read from
environment variables at start-up. That makes the "docker restart does not
re-read the env file" trap easy to see for yourself (see docker/LAB.md).

Run without Docker:   uvicorn day11_git_docker.docker.app:app --port 8000
Self-test (no server): python day11_git_docker/docker/app.py --selftest
"""
from __future__ import annotations

import os
import sys
import time

from fastapi import FastAPI

STARTED_AT = time.time()

# Read once, at process start. A container keeps the values it was created with.
MODEL_NAME = os.environ.get("MODEL_NAME", "fake-model")
APP_VERSION = os.environ.get("APP_VERSION", "dev")
API_KEY = os.environ.get("API_KEY")  # a secret: never returned, never logged

app = FastAPI(title="Day 11 model service")


@app.get("/health")
def health() -> dict:
    """Used by the Docker HEALTHCHECK and by the deploy checklist."""
    return {"status": "ok", "uptime_s": round(time.time() - STARTED_AT, 1)}


@app.get("/config")
def config() -> dict:
    """What this running container actually uses. Check it after every deploy."""
    return {
        "model": MODEL_NAME,
        "version": APP_VERSION,
        "api_key_set": API_KEY is not None,  # report presence only
    }


@app.get("/forecast")
def forecast(horizon: int = 5) -> dict:
    """A stand-in 'model': deterministic, so every container gives the same answer."""
    if not 1 <= horizon <= 63:
        return {"error": "INVALID_ARGUMENT", "message": "horizon must be 1..63"}
    value = round(4.0 + 0.01 * horizon, 4)
    return {"model": MODEL_NAME, "version": APP_VERSION, "horizon": horizon, "forecast": value}


def _selftest() -> None:
    from fastapi.testclient import TestClient

    c = TestClient(app)
    assert c.get("/health").json()["status"] == "ok"
    cfg = c.get("/config").json()
    assert "api_key" not in cfg and "api_key_set" in cfg
    assert c.get("/forecast", params={"horizon": 5}).json()["forecast"] == 4.05
    assert c.get("/forecast", params={"horizon": 99}).json()["error"] == "INVALID_ARGUMENT"
    print("day11 docker app selftest: OK")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=8000)
