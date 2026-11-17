"""Checks for the interview flashcards: interview_bank/make_flashcards.py and interview_bank/flashcards.csv.

The file sits in this folder because CI runs every test here (python -m pytest day15_testing -q).
Run:  python -m pytest day15_testing/test_flashcards.py -q
"""
from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("make_flashcards", ROOT / "interview_bank" / "make_flashcards.py")
fc = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = fc
_spec.loader.exec_module(fc)

SOURCES = fc.source_files(ROOT)


@pytest.fixture(scope="module")
def cards():
    return fc.build_cards(ROOT)


@pytest.mark.parametrize("pattern", [pattern for pattern, _ in fc.SOURCES])
def test_every_source_pattern_finds_a_file(pattern):
    assert any(path.match(pattern) for path, _ in SOURCES), f"no question file matches {pattern}"


@pytest.mark.parametrize("path, kind", SOURCES, ids=[fc.rel(path, ROOT) for path, _ in SOURCES])
def test_every_source_file_gives_a_card(path, kind):
    assert fc.cards_from_file(path, kind, ROOT), f"no questions found in {fc.rel(path, ROOT)}"


def test_no_empty_question_or_answer(cards):
    for card in cards:
        assert card.question.strip() and card.tags.strip(), card
        assert card.answer.split(" (more: ")[0].strip(), card
        for field in card:
            assert not field.startswith(("=", "+", "-", "@")), f"a spreadsheet would read this as a formula: {field}"


def test_no_duplicates(cards):
    questions = [card.question.casefold() for card in cards]
    repeated = sorted({q for q in questions if questions.count(q) > 1})
    assert not repeated, f"same question on more than one card: {repeated}"


def test_csv_round_trips(cards, tmp_path):
    tricky = fc.Card('A "quoted" question, with a comma?', "Answer; with a comma, and \"quotes\".", "test")
    path = tmp_path / "cards.csv"
    fc.write_csv([*cards, tricky], path)
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    assert tuple(rows[0]) == fc.FIELDS
    assert [fc.Card(*row) for row in rows[1:]] == [*cards, tricky]
    assert fc.read_csv(path) == [*cards, tricky]


def test_committed_csv_matches_the_question_files(cards):
    assert fc.read_csv(fc.OUT) == cards, "flashcards.csv is out of date: run python interview_bank/make_flashcards.py"


def test_answers_are_short_and_point_to_their_source(cards):
    for card in cards:
        body, pointer = card.answer.rsplit(" (more: ", 1)
        assert len(body.split()) <= fc.MAX_WORDS, card
        assert pointer.endswith(")") and (ROOT / pointer[:-1]).is_file(), card


def test_shorten_cuts_at_a_sentence_boundary():
    sentence = "This sentence has exactly ten words in it, you see. "
    assert fc.shorten(sentence * 9) == (sentence * 8).strip()          # 90 words: keep 8 whole sentences
    long_one = " ".join(["word"] * 100) + "."
    assert fc.shorten(long_one) == " ".join(["word"] * 80) + "..."     # no boundary in reach: cut at a word
