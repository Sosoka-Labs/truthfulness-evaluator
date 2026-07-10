"""Claim extraction using structured outputs."""

import asyncio
import re
from dataclasses import replace
from typing import List, Optional

from pydantic import BaseModel, Field

try:
    from refchecker.extractor import LLMExtractor

    REFCHECKER_AVAILABLE = True
except ImportError:
    REFCHECKER_AVAILABLE = False

from ...core.logging_config import get_logger
from ...core.segmentation import Sentence, segment_sentences
from ...models import Claim
from ..factory import create_chat_model
from ..prompts.extraction import (
    CLAIM_EXTRACTION_PROMPT,
    SENTENCE_SELECTION_PROMPT,
    TRIPLET_EXTRACTION_PROMPT,
)

logger = get_logger()

_VALID_CLAIM_TYPES = {"explicit", "implicit", "inferred"}
# Number of neighbouring sentences included on each side as claim context.
_CONTEXT_WINDOW = 1

# Fenced code blocks (```...``` / ~~~...~~~, optional language tag) and inline
# code spans. These hold example/illustrative content, not real project claims.
_FENCED_BLOCK = re.compile(r"(^|\n)(```|~~~)[^\n]*\n.*?\n\2(\s*\n|$)", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]+`")


def strip_example_blocks(text: str) -> str:
    """Remove fenced code blocks and inline code from document text.

    Fenced code blocks (``` ... ``` and ~~~ ... ~~~) often contain example
    output, code snippets, or illustrative scenarios that are not real
    assertions about the project. Removing them before extraction prevents
    false positives where the evaluator treats example claims as real claims.

    Inline code spans (`...`) are also stripped when they contain illustrative
    values rather than references to actual project entities.

    Args:
        text: Raw document text.

    Returns:
        Document text with example blocks replaced by whitespace.
    """
    text = _FENCED_BLOCK.sub(r"\1\n", text)
    text = _INLINE_CODE.sub("", text)
    return text


def example_block_spans(text: str) -> list[tuple[int, int]]:
    """Return character ranges of example blocks in ``text``.

    Unlike :func:`strip_example_blocks`, this reports spans against the original
    text so callers can exclude claims that fall inside example content without
    disturbing the source offsets used for verbatim slicing.

    Args:
        text: Raw document text.

    Returns:
        ``(start, end)`` half-open ranges for fenced blocks and inline code.
    """
    spans = [(m.start(), m.end()) for m in _FENCED_BLOCK.finditer(text)]
    spans += [(m.start(), m.end()) for m in _INLINE_CODE.finditer(text)]
    return spans


# Structured output models
class ExtractedClaim(BaseModel):
    """A single extracted claim."""

    text: str = Field(description="The claim text")
    claim_type: str = Field(description="Type: explicit, implicit, or inferred")


class ClaimExtractionOutput(BaseModel):
    """Output structure for claim extraction."""

    claims: List[ExtractedClaim] = Field(description="List of extracted claims")


class KnowledgeTriplet(BaseModel):
    """Subject-relation-object triplet."""

    subject: str = Field(description="The subject of the claim")
    relation: str = Field(description="The relationship/action")
    object: str = Field(description="The object/target")
    context: Optional[str] = Field(None, description="Additional context")


class TripletExtractionOutput(BaseModel):
    """Output structure for triplet extraction."""

    triplets: List[KnowledgeTriplet] = Field(description="List of knowledge triplets")


class SelectedSentence(BaseModel):
    """A sentence selected as claim-bearing, referenced by index."""

    index: int = Field(description="Index of the claim-bearing sentence")
    claim_type: str = Field(description="Type: explicit, implicit, or inferred")
    normalized_claim: Optional[str] = Field(
        None, description="Optional atomic restatement; never replaces the verbatim sentence"
    )


class SentenceSelectionOutput(BaseModel):
    """Output structure for sentence-index claim selection."""

    selections: List[SelectedSentence] = Field(
        description="Sentences selected as claim-bearing, referenced by index"
    )


class ClaimExtractionChain:
    """Extract factual claims from documents using RefChecker."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self._extractor = None

        if not REFCHECKER_AVAILABLE:
            raise ImportError("RefChecker not installed. Install with: pip install refchecker")

    @property
    def extractor(self):
        """Lazy initialization of extractor."""
        if self._extractor is None:
            self._extractor = LLMExtractor(model=self.model)
        return self._extractor

    async def extract(
        self, document: str, source_path: str, max_claims: Optional[int] = None
    ) -> list[Claim]:
        """
        Extract factual claims from document.

        Args:
            document: The document text to analyze
            source_path: Path/URL of the source document
            max_claims: Maximum number of claims to extract (None for all)

        Returns:
            List of Claim objects
        """
        # Strip example blocks before extraction to avoid false positives
        # from illustrative content in fenced code blocks and inline code.
        cleaned_document = strip_example_blocks(document)

        # Run extraction in thread pool (RefChecker is synchronous)
        triplets = await asyncio.to_thread(self._extract_triplets, cleaned_document)

        # Convert triplets to Claim objects
        claims = []
        for i, triplet in enumerate(triplets):
            if max_claims and i >= max_claims:
                break

            # Handle different triplet formats
            if isinstance(triplet, (list, tuple)) and len(triplet) >= 3:
                subject, relation, obj = triplet[0], triplet[1], triplet[2]
                claim_text = f"{subject} {relation} {obj}"
            elif isinstance(triplet, str):
                claim_text = triplet
            else:
                continue

            claim = Claim(
                id=f"claim_{i:03d}",
                text=claim_text,
                source_document=source_path,
                context=(
                    document[
                        max(0, document.find(claim_text) - 100) : min(
                            len(document), document.find(claim_text) + len(claim_text) + 100
                        )
                    ]
                    if claim_text in document
                    else None
                ),
            )
            claims.append(claim)

        return claims

    def _extract_triplets(self, document: str) -> list:
        """Extract triplets using RefChecker (synchronous)."""
        try:
            return self.extractor.extract(document)
        except Exception as e:
            logger.warning(f"RefChecker extraction failed: {e}")
            # Fallback: return empty list
            return []


class SimpleClaimExtractionChain:
    """Fallback claim extraction using structured LLM outputs."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self._llm = None

    @property
    def llm(self):
        """Lazy initialization of LLM with structured output."""
        if self._llm is None:
            base_llm = create_chat_model(self.model, temperature=0)
            # Use structured output
            self._llm = base_llm.with_structured_output(ClaimExtractionOutput)
        return self._llm

    async def extract(
        self, document: str, source_path: str, max_claims: Optional[int] = None
    ) -> list[Claim]:
        """Extract claims using structured LLM output."""
        # Strip example blocks before extraction to avoid false positives
        # from illustrative content in fenced code blocks and inline code.
        cleaned_document = strip_example_blocks(document)

        chain = CLAIM_EXTRACTION_PROMPT | self.llm

        try:
            result: ClaimExtractionOutput = await chain.ainvoke({"text": cleaned_document})

            claims = []
            for i, extracted in enumerate(result.claims):
                if max_claims and i >= max_claims:
                    break

                if extracted.text.strip():
                    claims.append(
                        Claim(
                            id=f"claim_{i:03d}",
                            text=extracted.text.strip(),
                            source_document=source_path,
                            claim_type=(
                                extracted.claim_type
                                if extracted.claim_type in ["explicit", "implicit", "inferred"]
                                else "explicit"
                            ),
                        )
                    )

            return claims

        except Exception as e:
            logger.warning(f"Simple extraction failed: {e}")
            return []


class TripletExtractionChain:
    """Extract claims as subject-relation-object triplets using structured output."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self._llm = None

    @property
    def llm(self):
        """Lazy initialization of LLM with structured output."""
        if self._llm is None:
            base_llm = create_chat_model(self.model, temperature=0)
            self._llm = base_llm.with_structured_output(TripletExtractionOutput)
        return self._llm

    async def extract(
        self, document: str, source_path: str, max_claims: Optional[int] = None
    ) -> list[Claim]:
        """Extract claims as triplets using structured output."""
        # Strip example blocks before extraction to avoid false positives
        # from illustrative content in fenced code blocks and inline code.
        cleaned_document = strip_example_blocks(document)

        chain = TRIPLET_EXTRACTION_PROMPT | self.llm

        try:
            result: TripletExtractionOutput = await chain.ainvoke({"text": cleaned_document})

            claims = []
            for i, triplet in enumerate(result.triplets):
                if max_claims and i >= max_claims:
                    break

                claim_text = f"{triplet.subject} {triplet.relation} {triplet.object}".strip()

                if claim_text:
                    claims.append(
                        Claim(
                            id=f"claim_{i:03d}",
                            text=claim_text,
                            source_document=source_path,
                            context=triplet.context,
                            claim_type="explicit",
                        )
                    )

            return claims

        except Exception as e:
            logger.warning(f"Triplet extraction failed: {e}")
            return []


class SentenceSelectionExtractionChain:
    """Extract claims by having the LLM select sentence indices, not rewrite text.

    The document is deterministically segmented into numbered sentences; the model
    returns the indices of claim-bearing sentences. Claim text is then sliced from
    the source by offset, so the quoted wording can never diverge from the document
    (misquote-proof by construction). ``Claim.source_span`` is populated accordingly.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self._llm = None

    @property
    def llm(self):
        """Lazy initialization of LLM with structured output."""
        if self._llm is None:
            base_llm = create_chat_model(self.model, temperature=0)
            self._llm = base_llm.with_structured_output(SentenceSelectionOutput)
        return self._llm

    async def extract(
        self, document: str, source_path: str, max_claims: Optional[int] = None
    ) -> list[Claim]:
        """Extract claims as verbatim sentences chosen by index."""
        # Segment the ORIGINAL document so every span indexes source_path exactly,
        # then drop sentences that fall inside example blocks (fenced / inline
        # code) so illustrative claims can never be selected.
        sentences = self._selectable_sentences(document)

        if not sentences:
            return []

        enumerated = "\n".join(f"[{s.index}] {s.text}" for s in sentences)
        chain = SENTENCE_SELECTION_PROMPT | self.llm

        try:
            result: SentenceSelectionOutput = await chain.ainvoke({"sentences": enumerated})
        except Exception as e:
            logger.warning(f"Sentence-selection extraction failed: {e}")
            return []

        return self._build_claims(result, sentences, source_path, max_claims)

    @staticmethod
    def _selectable_sentences(document: str) -> list[Sentence]:
        """Segment the document and exclude sentences inside example blocks.

        Spans are preserved against the original document; excluded sentences are
        re-indexed contiguously so the enumerated list handed to the LLM has no
        gaps.
        """
        excluded = example_block_spans(document)

        def in_example(sentence: Sentence) -> bool:
            return any(sentence.start < end and start < sentence.end for start, end in excluded)

        kept = [s for s in segment_sentences(document) if not in_example(s)]
        return [replace(s, index=i) for i, s in enumerate(kept)]

    def _build_claims(
        self,
        result: SentenceSelectionOutput,
        sentences: list[Sentence],
        source_path: str,
        max_claims: Optional[int],
    ) -> list[Claim]:
        """Convert validated selections into span-grounded Claim objects."""
        claims: list[Claim] = []
        seen: set[int] = set()

        for selection in result.selections:
            if max_claims and len(claims) >= max_claims:
                break

            idx = selection.index
            if not 0 <= idx < len(sentences):
                logger.warning(
                    f"Dropping out-of-range sentence index {idx} "
                    f"(document has {len(sentences)} sentences)"
                )
                continue
            if idx in seen:
                continue
            seen.add(idx)

            sentence = sentences[idx]
            claim_type = (
                selection.claim_type if selection.claim_type in _VALID_CLAIM_TYPES else "explicit"
            )
            claims.append(
                Claim(
                    id=f"claim_{len(claims):03d}",
                    text=sentence.text,
                    source_document=source_path,
                    source_span=(sentence.start, sentence.end),
                    context=self._context_for(sentences, idx),
                    normalized_text=selection.normalized_claim,
                    claim_type=claim_type,
                )
            )

        return claims

    @staticmethod
    def _context_for(sentences: list[Sentence], idx: int) -> Optional[str]:
        """Join a small window of neighbouring sentences as context."""
        lo = max(0, idx - _CONTEXT_WINDOW)
        hi = min(len(sentences), idx + _CONTEXT_WINDOW + 1)
        neighbours = [sentences[i].text for i in range(lo, hi) if i != idx]
        return " ".join(neighbours) if neighbours else None
