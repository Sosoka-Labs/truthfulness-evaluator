"""Claim extraction using structured outputs."""

import asyncio
from typing import List, Optional

from pydantic import BaseModel, Field

try:
    from refchecker.extractor import LLMExtractor

    REFCHECKER_AVAILABLE = True
except ImportError:
    REFCHECKER_AVAILABLE = False

from ...core.logging_config import get_logger
from ...models import Claim
from ..factory import create_chat_model
from ..prompts.extraction import CLAIM_EXTRACTION_PROMPT, TRIPLET_EXTRACTION_PROMPT

logger = get_logger()


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
        # Run extraction in thread pool (RefChecker is synchronous)
        triplets = await asyncio.to_thread(self._extract_triplets, document)

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

        chain = CLAIM_EXTRACTION_PROMPT | self.llm

        try:
            result: ClaimExtractionOutput = await chain.ainvoke({"text": document})

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

        chain = TRIPLET_EXTRACTION_PROMPT | self.llm

        try:
            result: TripletExtractionOutput = await chain.ainvoke({"text": document})

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
