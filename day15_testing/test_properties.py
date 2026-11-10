"""Layer 2: property-based tests with Hypothesis.

Instead of picking examples, state a rule that must hold for ALL inputs and let Hypothesis generate
hundreds of them, including nasty ones (empty strings, unicode, huge numbers). When it finds a failure
it shrinks it to the smallest input that breaks the rule.
LLMs send tools strange arguments, so 'never crashes, always returns a well-formed result' is the key property.
"""
from __future__ import annotations

import string

from hypothesis import given, settings
from hypothesis import strategies as st

from core.fund_model import rank_funds
from day12_llmops.guards import grounded_numbers
from day12_llmops.tracing import redact

SETTINGS = settings(max_examples=60, deadline=None)


@SETTINGS
@given(as_of=st.text(max_size=20), top_n=st.integers(min_value=-5, max_value=50))
def test_rank_funds_never_crashes_and_is_well_formed(as_of, top_n):
    out = rank_funds(as_of, top_n=top_n)
    assert isinstance(out, dict)
    if "error" in out:
        assert isinstance(out["error"], str) and out["error"]
    else:
        assert 1 <= len(out["top"]) <= top_n
        assert all(isinstance(r["predicted_return"], float) for r in out["top"])


@SETTINGS
@given(st.lists(st.floats(min_value=0.0001, max_value=0.05), min_size=1, max_size=5))
def test_numbers_copied_from_evidence_are_always_grounded(values):
    evidence = [{"fund": f"Fund {chr(65 + i)}", "predicted_return": round(v, 4)} for i, v in enumerate(values)]
    answer = " ".join(f"{e['fund']} {e['predicted_return'] * 100:.2f}%" for e in evidence)
    assert grounded_numbers(answer, evidence)["pass"]


@SETTINGS
@given(user=st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=12),
       noise=st.text(max_size=30))
def test_redact_never_leaks_an_email(user, noise):
    email = f"{user}@example.com"
    assert email not in redact(f"{noise} contact {email} {noise}")
