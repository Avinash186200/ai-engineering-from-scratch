"""Shared fixtures. pytest loads this file automatically for every test in the folder."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


@pytest.fixture()
def fixed_agent(monkeypatch):
    """The agent with the planted bug switched off (what the one-line fix does)."""
    from fi_agent import agent
    monkeypatch.setattr(agent, "DROP_CARRIED_AS_OF", False)
    return agent
