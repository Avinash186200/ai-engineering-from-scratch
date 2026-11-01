"""A resilient LLM adapter: retry with exponential backoff + jitter, failover, circuit breaker,
and an overall deadline. Fatal errors (a malformed request) are never retried.

Providers here are fakes by default. Run the three scenarios:
    python day08_production/llm_adapter.py
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.llm import FakeLLM  # noqa: E402

LLMResult = dict          # {"text": str, "tool_calls": [...]}, same as core/llm.py


class RetryableError(Exception):
    """Worth trying again: overloaded, rate limited, timeout."""


class FatalError(Exception):
    """Never retry: a malformed request or a bad key. Goes straight up."""


class LLMUnavailable(Exception):
    """Every provider failed, or the deadline ran out."""


class CircuitBreaker:
    """After `threshold` consecutive failures, skip the provider for `cooldown` seconds."""

    def __init__(self, threshold=3, cooldown=30.0):
        self.threshold, self.cooldown = threshold, cooldown
        self.failures, self.opened_at = 0, None

    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.monotonic() - self.opened_at >= self.cooldown:   # half-open: allow a trial call
            return False
        return True

    def success(self):
        self.failures, self.opened_at = 0, None

    def failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.opened_at = time.monotonic()


class FakeProvider:
    """Fails the first `fail_times` calls with RetryableError, then answers like FakeLLM."""

    def __init__(self, name, fail_times=0, inner=None):
        self.name, self.fail_times, self.calls = name, fail_times, 0
        self.inner = inner or FakeLLM()

    def complete(self, system, messages, tools=None) -> LLMResult:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RetryableError(f"{self.name}: overloaded (call {self.calls})")
        return self.inner.complete(system, messages, tools)


class ClaudeProvider:
    """Real Claude, with SDK errors mapped to RetryableError / FatalError."""

    name = "claude"

    def __init__(self):
        import anthropic
        from core.llm import ClaudeLLM
        self.llm, self.anthropic = ClaudeLLM(), anthropic

    def complete(self, system, messages, tools=None) -> LLMResult:
        a = self.anthropic
        try:
            return self.llm.complete(system, messages, tools)
        except (a.RateLimitError, a.APITimeoutError, a.APIConnectionError, a.InternalServerError) as e:
            raise RetryableError(str(e)) from e
        except a.APIStatusError as e:
            raise FatalError(str(e)) from e


class ResilientLLM:
    def __init__(self, providers, attempts=3, deadline_s=20.0, log=print):
        self.providers, self.attempts, self.deadline_s, self.log = providers, attempts, deadline_s, log
        self.breaker = {p.name: CircuitBreaker() for p in providers}

    def complete(self, system, messages, tools=None) -> LLMResult:
        deadline = time.monotonic() + self.deadline_s
        for provider in self.providers:              # FAILOVER
            if self.breaker[provider.name].is_open():
                self.log(f"  [{provider.name}] circuit open, skipping")
                continue                             # skip a dead provider
            for attempt in range(self.attempts):     # RETRY
                try:
                    result = provider.complete(system, messages, tools)
                    self.breaker[provider.name].success()
                    return result
                except RetryableError as exc:
                    self.breaker[provider.name].failure()
                    if self.breaker[provider.name].is_open():
                        self.log(f"  [{provider.name}] {exc}; breaker opens, failing over")
                        break
                    wait = 0.5 * 2 ** attempt + random.uniform(0, 0.5)
                    if time.monotonic() + wait > deadline:
                        raise LLMUnavailable("deadline")
                    self.log(f"  [{provider.name}] {exc}; retry in {wait:.2f}s")
                    time.sleep(wait)
        raise LLMUnavailable("all providers failed")


def default_llm(providers=("fake",), log=lambda *_: None) -> ResilientLLM:
    """Build the adapter from a provider list such as LLM_PROVIDERS=claude,fake."""
    def make(name):
        if name == "claude":
            return ClaudeProvider()
        if name == "down":                       # a provider that always fails, for demos
            return FakeProvider("down", fail_times=10**9)
        return FakeProvider(name or "fake")
    built = [make(p.strip()) for p in providers]
    return ResilientLLM(built, log=log)


if __name__ == "__main__":
    random.seed(0)
    msgs = [{"role": "user", "content": "hello"}]
    print("1) flaky primary recovers after 2 retries:")
    llm = ResilientLLM([FakeProvider("primary", fail_times=2), FakeProvider("backup")])
    print("  ->", llm.complete("", msgs)["text"])
    print("2) primary down: the breaker opens and we fail over:")
    llm = ResilientLLM([FakeProvider("primary", fail_times=99), FakeProvider("backup")])
    print("  ->", llm.complete("", msgs)["text"])
    print("3) next call skips the open circuit immediately:")
    print("  ->", llm.complete("", msgs)["text"])
    print("4) everything down:")
    try:
        ResilientLLM([FakeProvider("only", fail_times=99)]).complete("", msgs)
    except LLMUnavailable as exc:
        print("  -> LLMUnavailable:", exc)
