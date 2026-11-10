"""Shared fixtures. pytest loads this file automatically for every test in the folder."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def chat_app():
    """The Day 8 FastAPI app, loaded once per test session (building the agent is the slow part)."""
    spec = importlib.util.spec_from_file_location("chat_app", ROOT / "day08_production" / "app.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def client(chat_app):
    from fastapi.testclient import TestClient
    return TestClient(chat_app.app)


@pytest.fixture(scope="session")
def a_business_day() -> str:
    return "2025-06-19"
