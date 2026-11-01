"""A resilient LLM adapter: retry with exponential backoff + jitter, failover, circuit breaker.

Providers here are fakes by default (one flaky, one reliable). Run the demo:
    python day08_production/llm_adapter.py
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.llm import FakeLLM  # noqa: E402


class ProviderError(Exception):
    pass


class FlakyProvider:
    """Fails the first `fail_times` calls (like an overloaded error or a timeout), then works."""

    def __init__(self, name, fail_times=2, inner=None):
        self.name, self.fail_times, self.calls = name, fail_times, 0
        self.inner = inner or FakeLLM()

    def complete(self, system, messages, tools=None):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise ProviderError(f"{self.name}: overloaded (call {self.calls})")
        return self.inner.complete(system, messages, tools)


class CircuitBreaker:
    """After `threshold` consecutive failures, skip the provider for `cooldown` seconds."""

    def __init__(self, threshold=3, cooldown=30.0):
        self.threshold, self.cooldown = threshold, cooldown
        self.failures, self.opened_at = 0, None

    def allow(self):
        if self.opened_at is None:
            return True
        return time.monotonic() - self.opened_at >= self.cooldown   # half-open after cooldown

    def record(self, ok):
        if ok:
            self.failures, self.opened_at = 0, None
        else:
            self.failures += 1
            if self.failures >= self.threshold:
                self.opened_at = time.monotonic()


class ResilientLLM:
    def __init__(self, providers, retries=2, base_delay=0.05, log=print):
        self.providers = providers
        self.breakers = {p.name: CircuitBreaker() for p in providers}
        self.retries, self.base_delay, self.log = retries, base_delay, log

    def complete(self, system, messages, tools=None):
        for p in self.providers:
            br = self.breakers[p.name]
            if not br.allow():
                self.log(f"  [{p.name}] circuit open, skipping")
                continue
            for attempt in range(self.retries + 1):
                try:
                    out = p.complete(system, messages, tools)
                    br.record(True)
                    return out
                except ProviderError as e:
                    br.record(False)
                    if not br.allow() or attempt == self.retries:
                        self.log(f"  [{p.name}] {e}")
                        break
                    delay = self.base_delay * 2 ** attempt * (1 + random.random() / 2)
                    self.log(f"  [{p.name}] {e}; retry in {delay:.2f}s")
                    time.sleep(delay)
            self.log(f"  [{p.name}] giving up, failing over")
        raise ProviderError("all providers failed")


def default_llm(real=False, log=lambda *_: None):
    """Primary: Claude if real else a fake; backup: always the deterministic FakeLLM."""
    if real:
        from core.llm import ClaudeLLM
        primary = FlakyProvider("claude", fail_times=0, inner=ClaudeLLM())
    else:
        primary = FlakyProvider("primary-fake", fail_times=0)
    return ResilientLLM([primary, FlakyProvider("backup-fake", fail_times=0)], log=log)


if __name__ == "__main__":
    random.seed(0)
    msgs = [{"role": "user", "content": "hello"}]
    print("1) flaky primary recovers after 2 retries:")
    llm = ResilientLLM([FlakyProvider("primary", fail_times=2), FlakyProvider("backup", 0)])
    print("  ->", llm.complete("", msgs)["text"])
    print("2) primary down: breaker opens and we fail over:")
    llm = ResilientLLM([FlakyProvider("primary", fail_times=99), FlakyProvider("backup", 0)])
    print("  ->", llm.complete("", msgs)["text"])
    print("3) next call skips the open circuit immediately:")
    print("  ->", llm.complete("", msgs)["text"])
