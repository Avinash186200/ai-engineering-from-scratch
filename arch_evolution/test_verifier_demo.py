from arch_evolution.verifier_demo import answer, tokenize

TABLE = tokenize([{"name": "x", "ret": 0.99, "vol": 12.4, "flag": True}])


def test_tokens_cover_numbers_only():
    assert set(TABLE) == {"c1.n0", "c1.n1"}


def test_grounded_answer_is_rendered_by_code():
    out = answer("Return {c1.n0}, vol {c1.n1}.", TABLE)
    assert out == {"status": "ok", "text": "Return 0.99 (ret), vol 12.40 (vol)."}


def test_number_typed_by_model_is_rejected():
    assert answer("Return is 1.5 percent.", TABLE)["errors"] == ["DIGIT_IN_TEXT"]


def test_unknown_token_is_rejected():
    assert answer("Return {c9.n0}.", TABLE)["errors"] == ["UNKNOWN_TOKEN:c9.n0"]
