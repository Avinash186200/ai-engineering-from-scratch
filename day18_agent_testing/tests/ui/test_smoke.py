"""Browser smoke test for the chat page. Skipped cleanly if Playwright is not installed.

    pip install pytest-playwright && python -m playwright install chromium
"""
from __future__ import annotations

import importlib.util
import threading
from pathlib import Path

import pytest

sync_api = pytest.importorskip("playwright.sync_api")

APP = Path(__file__).resolve().parents[2] / "web" / "app.py"


@pytest.fixture(scope="module")
def base_url_live():
    spec = importlib.util.spec_from_file_location("fi_chat_app", APP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    srv = mod.make_server(port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def test_two_turn_chat_carries_the_date(base_url_live):
    with sync_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:  # browser binaries not downloaded
            pytest.skip(f"chromium not available: {e}")
        page = browser.new_page()
        page.goto(base_url_live)
        page.fill("#msg", "What is the OAS of POOL-A30 as of 2026-11-12?")
        page.click("#send")
        page.wait_for_selector("[data-testid=answer]")
        page.fill("#msg", "And its duration as of then?")
        page.click("#send")
        page.wait_for_function("document.querySelectorAll('[data-testid=answer]').length == 2")
        answers = page.locator("[data-testid=answer]").all_inner_texts()
        browser.close()
    assert "48.2" in answers[0]
    assert "5.91" in answers[1] and "2026-11-12" in answers[1]
