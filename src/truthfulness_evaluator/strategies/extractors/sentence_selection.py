"""Sentence-index (span-grounded) claim extraction adapter."""

from ...llm.chains.extraction import SentenceSelectionExtractionChain
from ...models import Claim


class SentenceSelectionExtractor:
    """Adapter for SentenceSelectionExtractionChain satisfying ClaimExtractor.

    The model selects claim-bearing sentences by index; claim text is sliced
    verbatim from the source, so extracted claims are guaranteed to quote the
    document exactly and ``Claim.source_span`` is populated.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self._chain = SentenceSelectionExtractionChain(model=model)

    async def extract(
        self,
        document: str,
        source_path: str,
        *,
        max_claims: int | None = None,
    ) -> list[Claim]:
        """Extract claims as verbatim sentences chosen by index."""
        return await self._chain.extract(
            document=document,
            source_path=source_path,
            max_claims=max_claims,
        )
