"""Simple claim extraction adapter."""

from ..chains.extraction import SimpleClaimExtractionChain
from ..models import Claim


class SimpleExtractor:
    """Adapter for SimpleClaimExtractionChain satisfying ClaimExtractor protocol."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self._chain = SimpleClaimExtractionChain(model=model)

    async def extract(
        self,
        document: str,
        source_path: str,
        *,
        max_claims: int | None = None,
    ) -> list[Claim]:
        """Extract claims using simple LLM-based extraction."""
        return await self._chain.extract(
            document=document,
            source_path=source_path,
            max_claims=max_claims,
        )
