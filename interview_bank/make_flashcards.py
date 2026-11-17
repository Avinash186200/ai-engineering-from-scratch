"""Turn every question-and-answer file in this repo into one flashcard deck.

Run:  python interview_bank/make_flashcards.py

Writes interview_bank/flashcards.csv with three columns: question, answer, tags. Each answer is the first
sentences of the full answer (about 80 words) followed by "(more: <file>)", the file with the rest. The tag
is the topic, taken from the file name (or the folder name for INTERVIEW_QA.md and README.md). Standard
library only, and every run gives the same file.

The question formats it reads:
- "### 3. Question" with the answer in the lines below (interview_bank, arch_evolution, lessons_learned).
  The day folders put a hidden "Understand it" block first and the answer on a "**Answer:**" line.
- "## 3. Question" with a video link, a bold headline and a quote around the answer (interview_special).
- '- "Question" answer' bullets under a "probes" heading (system_design). The rest of those files are
  design walkthroughs, not questions, so only the probes are used.

Typographic dashes and quotes become plain ASCII, so the file opens cleanly in any spreadsheet, and a text
that starts with = + - or @ gets its first word in quotes, so a spreadsheet does not read it as a formula.
A question asked in two files gets its topic added in brackets the second time, so every card front is unique.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "interview_bank" / "flashcards.csv"
FIELDS = ("question", "answer", "tags")
MAX_WORDS = 80

# Where the questions live, in deck order, and which reader each file needs.
SOURCES = (
    ("interview_bank/*.md", "numbered"),
    ("day*/INTERVIEW_QA.md", "numbered"),
    ("arch_evolution/INTERVIEW_QA.md", "numbered"),
    ("lessons_learned/INTERVIEW_QA.md", "numbered"),
    ("interview_special/README.md", "numbered"),
    ("system_design/*.md", "probes"),
)
SKIP = {"interview_bank/README.md"}

QUESTION = re.compile(r"^#{2,3}\s+\d+\.\s+(.+?)\s*$")         # "### 3. Question" or "## 3. Question"
HEADING = re.compile(r"^#{1,6}\s")
DETAILS = re.compile(r"<details>.*?</details>", re.S)          # the day folders' "Understand it" blocks
FENCE = re.compile(r"^```.*?^```[^\n]*$", re.S | re.M)
LINK_ONLY = re.compile(r"^\[[^\]]+\]\([^)]+\)$")                # "[Watch at 0:16](...)"
BOLD_ONLY = re.compile(r"^\*\*[^*]+\*\*$")                      # a headline that repeats the first sentence
ANSWER_LABEL = re.compile(r"^\*\*Answer:\*\*\s*")
BOLD_LABEL = re.compile(r"^\*\*([^*]+?)[.:]\*\*\s*")            # "**Challenge.** text" -> "Challenge: text"
LIST_MARK = re.compile(r"^(?:[-*+]|\d+\.)\s+")
HTML_TAG = re.compile(r"</?(?:details|summary|br|p|span|sup|sub|kbd|code|b|i|em|strong)\b[^>]*>", re.I)
PROBES_HEADING = re.compile(r"^##\s+.*\bprobes\b", re.I | re.M)
PROBE = re.compile(r'^"([^"]+)"\s+(.+)$')                       # '"Question?" answer'
DESIGN_TITLE = re.compile(r"^#\s+Design\s+\d+:\s*(.+?)\s*$", re.M)
SENTENCE_END = re.compile(r"[.!?][\"')\]]*(?=\s+[\"'(\[]?[A-Z0-9])")
ABBREVIATIONS = ("e.g.", "i.e.", "vs.", "cf.")
# Typographic characters to plain ASCII: dashes, curly quotes, ellipsis, arrow, non-breaking space.
PLAIN = str.maketrans({chr(0x2014): "-", chr(0x2013): "-", chr(0x2018): "'", chr(0x2019): "'",
                       chr(0x201C): '"', chr(0x201D): '"', chr(0x2026): "...", chr(0x2192): "->", chr(0xA0): " "})


class Card(NamedTuple):
    """One CSV row."""

    question: str
    answer: str
    tags: str


def rel(path: Path, root: Path = ROOT) -> str:
    return path.relative_to(root).as_posix()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def source_files(root: Path = ROOT) -> list[tuple[Path, str]]:
    """Every question file in deck order, with the name of the reader it needs."""
    found = []
    for pattern, kind in SOURCES:
        for path in sorted(root.glob(pattern), key=lambda p: rel(p, root)):
            if rel(path, root) in SKIP:
                continue
            if kind == "probes" and not PROBES_HEADING.search(read(path)):
                continue  # a design walkthrough or template with no question list
            found.append((path, kind))
    return found


def topic(path: Path) -> str:
    """'interview_bank/rag_in_practice.md' -> 'rag_in_practice', 'day12_llmops/INTERVIEW_QA.md' -> 'llmops'."""
    name = path.parent.name if path.stem in ("INTERVIEW_QA", "README") else path.stem
    return re.sub(r"^(?:day)?\d+_", "", name).lower()


def clean(text: str) -> str:
    """Markdown to plain text on one line."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)          # images
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)      # links keep their text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)              # bold
    text = HTML_TAG.sub("", text.replace("`", ""))
    return " ".join(text.translate(PLAIN).split())


def answer_text(lines: list[str]) -> str:
    kept = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith((">", "|")) or s in ("---", "***", "___"):
            continue  # blank lines, quotes (a repeated key line), tables, rules
        if LINK_ONLY.match(s) or BOLD_ONLY.match(s):
            continue
        s = BOLD_LABEL.sub(r"\1: ", ANSWER_LABEL.sub("", s))
        kept.append(LIST_MARK.sub("", s))
    return clean(" ".join(kept))


def parse_numbered(text: str) -> list[tuple[str, str]]:
    """(question, full answer) for each numbered question heading."""
    text = FENCE.sub("", DETAILS.sub("", text))
    pairs: list[tuple[str, str]] = []
    question, body = None, []
    for line in text.split("\n"):
        if HEADING.match(line):
            if question is not None:
                pairs.append((question, answer_text(body)))
            match = QUESTION.match(line)
            question, body = (clean(match.group(1)) if match else None), []
        elif question is not None:
            body.append(line)
    if question is not None:
        pairs.append((question, answer_text(body)))
    return pairs


def parse_probes(text: str) -> list[tuple[str, str]]:
    """(question, answer) for each '- "Question" answer' bullet under a probes heading."""
    title = DESIGN_TITLE.search(text)
    context = f"System design ({title.group(1)})" if title else "System design"
    bullets: list[str] = []
    in_probes = False
    for line in FENCE.sub("", text).split("\n"):
        if HEADING.match(line):
            in_probes = bool(PROBES_HEADING.match(line))
        elif in_probes and line.startswith("- "):
            bullets.append(line[2:].strip())
        elif in_probes and bullets and line.startswith((" ", "\t")) and line.strip():
            bullets[-1] += " " + line.strip()  # a bullet that wraps onto the next line
    pairs = []
    for bullet in bullets:
        match = PROBE.match(clean(bullet))
        if match:
            question, answer = match.groups()
            if not question.endswith("?"):
                question += " What do you do?"
            pairs.append((f"{context}: {question}", answer))
    return pairs


def split_sentences(text: str) -> list[str]:
    sentences, start = [], 0
    for match in SENTENCE_END.finditer(text):
        if text[: match.end()].lower().endswith(ABBREVIATIONS):
            continue
        sentences.append(text[start : match.end()].strip())
        start = match.end()
    rest = text[start:].strip()
    return sentences + [rest] if rest else sentences


def shorten(text: str, max_words: int = MAX_WORDS) -> str:
    """The first whole sentences that fit in max_words. A first sentence that is too long is cut at a word."""
    kept, count = [], 0
    for sentence in split_sentences(text):
        words = len(sentence.split())
        if count + words > max_words:
            break
        kept.append(sentence)
        count += words
    if kept:
        return " ".join(kept)
    return " ".join(text.split()[:max_words]).rstrip(",;:") + "..."


def no_formula(text: str) -> str:
    """'-p publishes a port' -> '"-p" publishes a port'."""
    if text.startswith(("=", "+", "-", "@")):
        first, _, rest = text.partition(" ")
        return f'"{first}" {rest}'.rstrip()
    return text


PARSERS = {"numbered": parse_numbered, "probes": parse_probes}


def cards_from_file(path: Path, kind: str, root: Path = ROOT) -> list[Card]:
    where = rel(path, root)
    return [
        Card(no_formula(question), f"{no_formula(shorten(answer))} (more: {where})", topic(path))
        for question, answer in PARSERS[kind](read(path))
        if question and answer
    ]


def cards_by_file(root: Path = ROOT) -> list[tuple[Path, list[Card]]]:
    seen: set[str] = set()
    per_file = []
    for path, kind in source_files(root):
        cards = []
        for card in cards_from_file(path, kind, root):
            if card.question.casefold() in seen:
                card = card._replace(question=f"{card.question} ({card.tags})")
            seen.add(card.question.casefold())
            cards.append(card)
        per_file.append((path, cards))
    return per_file


def build_cards(root: Path = ROOT) -> list[Card]:
    return [card for _, cards in cards_by_file(root) for card in cards]


def write_csv(cards: list[Card], path: Path = OUT) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(FIELDS)
        writer.writerows(cards)


def read_csv(path: Path = OUT) -> list[Card]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    if not rows or tuple(rows[0]) != FIELDS:
        raise ValueError(f"{path} does not start with the header {','.join(FIELDS)}")
    return [Card(*row) for row in rows[1:]]


def main() -> None:
    per_file = cards_by_file()
    cards = [card for _, file_cards in per_file for card in file_cards]
    write_csv(cards)
    width = max(len(rel(path)) for path, _ in per_file)
    for path, file_cards in per_file:
        print(f"{rel(path):<{width}}  {len(file_cards):>3}")
    print(f"{'total':<{width}}  {len(cards):>3}  -> {rel(OUT)}")


if __name__ == "__main__":
    main()
