"""Post-deploy smoke test: is the thing we just deployed really live, and really the right version?

A deploy is not done when the command returns. It is done when these pass against the real URL:
  1. /health answers ok, fast
  2. /config reports the version we meant to ship (catches 'old container still running')
  3. the secret is present (reported as a yes/no, never the value)
  4. a real model call gives the known answer (catches a broken model file or wrong config)
  5. a bad input gets a clean error, not a crash
Exit code 0 = pass, 1 = fail, so a CI job or deploy script can roll back automatically.

Run against a deployed service:  python day13_cloud/smoke_test.py https://my-service.run.app --version main-ce57d87
Self-test, no cloud, no server:   python day13_cloud/smoke_test.py --selftest
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LATENCY_BUDGET_MS = 2000


def http_get(base: str):
    def get(path: str):
        t0 = time.perf_counter()
        with urllib.request.urlopen(base.rstrip("/") + path, timeout=10) as r:
            body = json.loads(r.read().decode())
            return r.status, body, (time.perf_counter() - t0) * 1000
    return get


def run_checks(get, expected_version: str | None) -> list[tuple[str, bool, str]]:
    results = []

    def check(name, fn):
        try:
            ok, detail = fn()
        except Exception as e:                       # a check that crashes is a failed check
            ok, detail = False, f"{type(e).__name__}: {e}"
        results.append((name, ok, detail))

    def health():
        status, body, ms = get("/health")
        return status == 200 and body.get("status") == "ok" and ms < LATENCY_BUDGET_MS, f"{status} {body} {ms:.0f} ms"

    def version():
        _, body, _ = get("/config")
        if expected_version is None:
            return True, f"running {body.get('version')} (no expected version given)"
        return body.get("version") == expected_version, f"running {body.get('version')}, expected {expected_version}"

    def secret():
        _, body, _ = get("/config")
        leaked = any("key" in k and k != "api_key_set" for k in body)
        return body.get("api_key_set") is True and not leaked, f"api_key_set={body.get('api_key_set')}"

    def model_call():
        _, body, _ = get("/forecast?horizon=5")
        return body.get("forecast") == 4.05, f"forecast={body.get('forecast')}"

    def bad_input():
        status, body, _ = get("/forecast?horizon=999")
        return status == 200 and body.get("error") == "INVALID_ARGUMENT", f"{status} {body.get('error')}"

    for name, fn in [("health", health), ("version", version), ("secret present", secret),
                     ("model answer", model_call), ("bad input handled", bad_input)]:
        check(name, fn)
    return results


def report(results) -> bool:
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:18} {detail}")
    passed = all(ok for _, ok, _ in results)
    print("SMOKE TEST", "PASSED" if passed else "FAILED: roll back")
    return passed


def _selftest() -> None:
    """Runs the same checks in-process against the Day 11 app, twice: good deploy and stale deploy."""
    import importlib
    import os
    from fastapi.testclient import TestClient

    def client_for(version: str, key: str | None):
        os.environ["APP_VERSION"] = version
        if key:
            os.environ["API_KEY"] = key
        else:
            os.environ.pop("API_KEY", None)
        mod = importlib.reload(importlib.import_module("day11_git_docker.docker.app"))
        c = TestClient(mod.app)

        def get(path):
            t0 = time.perf_counter()
            r = c.get(path)
            return r.status_code, r.json(), (time.perf_counter() - t0) * 1000
        return get

    print("Deploy A: new version, key set")
    good = report(run_checks(client_for("main-ce57d87", "fake-key"), "main-ce57d87"))
    print("\nDeploy B: old container still running, key missing")
    bad = report(run_checks(client_for("main-1a2b3c4", None), "main-ce57d87"))
    assert good and not bad
    print("\nselftest ok: good deploy passes, stale deploy is caught")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    elif len(sys.argv) > 1:
        ver = sys.argv[sys.argv.index("--version") + 1] if "--version" in sys.argv else None
        sys.exit(0 if report(run_checks(http_get(sys.argv[1]), ver)) else 1)
    else:
        print(__doc__)
