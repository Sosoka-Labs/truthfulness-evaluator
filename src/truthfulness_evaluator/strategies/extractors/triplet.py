"""Triplet-based claim extraction adapter."""

from ...llm.chains.extraction import TripletExtractionChain
from ...models import Claim


class TripletExtractor:
    """Adapter for TripletExtractionChain satisfying ClaimExtractor protocol."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self._chain = TripletExtractionChain(model=model)

    async def extract(
        self,
        document: str,
        source_path: str,
        *,
        max_claims: int | None = None,
    ) -> list[Claim]:
        """Extract claims as subject-relation-object triplets."""
        return await self._chain.extract(
            document=document,
            source_path=source_path,
            max_claims=max_claims,
        )
