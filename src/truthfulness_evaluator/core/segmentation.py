"""Deterministic sentence segmentation with preserved character offsets.

This module underpins span-grounded claim extraction. Instead of letting an LLM
rewrite claim text (which risks misquoting the source), we split a document into
enumerated sentences and let the model select sentences by index. The verbatim
claim text is then sliced from the source by offset, making misquotes impossible
by construction.

The one invariant every consumer relies on:

    document[sentence.start : sentence.end] == sentence.text

No third-party NLP dependency is used -- segmentation is a small, auditable set of
rules tuned for technical documentation and Markdown prose.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass

__all__ = ["Sentence", "segment_sentences"]


# Abbreviations that end in a period but do NOT terminate a sentence. Kept small
# and lowercase; matching is case-insensitive on the trailing token.
_ABBREVIATIONS: frozenset[str] = frozenset(
    {
        "e.g.",
        "i.e.",
        "etc.",
        "vs.",
        "dr.",
        "mr.",
        "mrs.",
        "ms.",
        "prof.",
        "st.",
        "no.",
        "fig.",
        "al.",  # et al.
        "cf.",
        "approx.",
        "inc.",
        "ltd.",
        "co.",
    }
)

# A sentence terminator is one of . ! ? (optionally repeated / followed by a
# closing quote or bracket) that is followed by whitespace or end-of-text.
_TERMINATOR = re.compile(r'([.!?]+)(["\')\]]*)(\s+|$)')

# Trailing token immediately before a candidate terminator, used to veto splits
# after abbreviations (e.g. "Dr.") and numeric decimals/versions (e.g. "3.11").
_TRAILING_TOKEN = re.compile(r"(\S+)$")
_ENDS_WITH_DIGIT = re.compile(r"\d$")


@dataclass(frozen=True)
class Sentence:
    """A single sentence with its verbatim text and source character span.

    Attributes:
        index: Zero-based position in the sentence list.
        text: Verbatim slice of the source; equals ``document[start:end]``.
        start: Inclusive character offset in the source document.
        end: Exclusive character offset in the source document.
    """

    index: int
    text: str
    start: int
    end: int


# A dotted acronym such as "U.S." or "Ph.D." -- runs of single letters each
# followed by a period. Treated as non-terminating.
_DOTTED_ACRONYM = re.compile(r"([A-Za-z]\.){2,}$")
# An ordered-list marker ("1." / "2)") sitting at the start of its line.
_ORDERED_MARKER = re.compile(r"\d+[.)]$")


def _is_hard_boundary(document: str, term_end: int) -> bool:
    """Whether a terminator at ``term_end`` ends a sentence.

    Vetoes splits that fall right after a known abbreviation, a numeric literal
    (decimals, version strings), a dotted acronym, or an ordered-list marker --
    each of which would otherwise fragment a claim (e.g. "version 3.11" into
    "version 3." + "11", or "1. Install it." into "1." + "Install it.").
    """
    preceding = document[:term_end]
    token_match = _TRAILING_TOKEN.search(preceding)
    if token_match is None:
        return True

    token = token_match.group(1)
    if token.lower() in _ABBREVIATIONS:
        return False

    # Single capital letter followed by a period -> initial (e.g. "J. Doe").
    if len(token) == 2 and token[0].isupper() and token[1] == ".":
        return False

    # Dotted acronym (e.g. "U.S.", "Ph.D.").
    if _DOTTED_ACRONYM.match(token):
        return False

    # Ordered-list marker at the start of a line ("1." / "2)") -> keep the
    # marker attached to the item text rather than splitting it off.
    if _ORDERED_MARKER.match(token):
        line_prefix = document[: token_match.start(1)].rsplit("\n", 1)[-1]
        if line_prefix.strip(" \t") == "":
            return False

    # Decimal / version number: digit immediately before the '.' terminator and
    # a digit immediately after it (e.g. "3.11", "100.5").
    if token.endswith(".") and _ENDS_WITH_DIGIT.search(token[:-1] or ""):
        after = document[term_end:]
        if after[:1].isdigit():
            return False

    return True


def _emit(sentences: list[Sentence], document: str, start: int, end: int) -> None:
    """Append a trimmed sentence if it holds non-whitespace content.

    Leading/trailing whitespace is excluded from the span so the stored offsets
    bracket real content, preserving the verbatim slice invariant.
    """
    raw = document[start:end]
    if not raw.strip():
        return

    lead = len(raw) - len(raw.lstrip())
    trail = len(raw) - len(raw.rstrip())
    true_start = start + lead
    true_end = end - trail
    sentences.append(
        Sentence(
            index=len(sentences),
            text=document[true_start:true_end],
            start=true_start,
            end=true_end,
        )
    )


def segment_sentences(document: str) -> list[Sentence]:
    """Split ``document`` into sentences with preserved character offsets.

    Boundaries are drawn at sentence terminators (``.``/``!``/``?`` followed by
    whitespace), at blank-line paragraph breaks, and at Markdown structural lines
    (headings, list items). Abbreviations and numeric literals are protected from
    spurious splitting.

    Args:
        document: The source text to segment (already stripped of example blocks
            by the caller, if desired).

    Returns:
        Sentences in document order, each satisfying
        ``document[s.start:s.end] == s.text``. Whitespace-only spans are omitted,
        so indices are contiguous over real content.
    """
    sentences: list[Sentence] = []

    # First partition into blocks on blank lines and Markdown structural lines.
    # Each block is then split on sentence terminators. This keeps list items and
    # headings as independent, individually selectable units.
    for block_start, block_end in _iter_blocks(document):
        cursor = block_start
        for match in _TERMINATOR.finditer(document, block_start, block_end):
            term_end = match.end(2)  # end of punctuation + closing quotes
            if not _is_hard_boundary(document, term_end):
                continue
            _emit(sentences, document, cursor, term_end)
            cursor = match.end()  # skip the trailing whitespace
        # Trailing content in the block with no terminator.
        if cursor < block_end:
            _emit(sentences, document, cursor, block_end)

    return sentences


def _iter_blocks(document: str) -> Iterator[tuple[int, int]]:
    """Yield ``(start, end)`` spans for structural blocks of the document.

    A block break occurs at a blank line (paragraph break) or at the start of a
    Markdown heading (``#``) or list item (``-``/``*``/``+``/ordered). Yielding
    spans (not substrings) keeps every downstream offset anchored to the source.
    """
    lines = document.splitlines(keepends=True)
    block_start = 0
    pos = 0
    prev_was_break = True

    for line in lines:
        line_start = pos
        pos += len(line)
        stripped = line.strip()

        is_blank = stripped == ""
        is_structural = bool(re.match(r"(#{1,6}\s|[-*+]\s|\d+[.)]\s)", stripped))

        if is_blank:
            if block_start < line_start:
                yield (block_start, line_start)
            block_start = pos
            prev_was_break = True
            continue

        # A structural line starts its own block, unless it is already the block
        # start (avoids emitting an empty leading block).
        if is_structural and not prev_was_break and block_start < line_start:
            yield (block_start, line_start)
            block_start = line_start

        prev_was_break = False

    if block_start < len(document):
        yield (block_start, len(document))
