"""Web search evidence gatherer adapter."""

from typing import Any

from ...core.logging_config import get_logger
from ...evidence.tools.web_search import WebEvidenceGatherer
from ...models import Claim, Evidence

logger = get_logger()


class WebSearchGatherer:
    """Adapter wrapping WebEvidenceGatherer for the EvidenceGatherer protocol."""

    def __init__(self, max_results: int = 3):
        """Initialize web search gatherer.

        Args:
            max_results: Maximum number of search results to gather
        """
        self._max_results = max_results
        self._gatherer = WebEvidenceGatherer()

    async def gather(self, claim: Claim, context: dict[str, Any]) -> list[Evidence]:
        """Gather web evidence for a claim.

        Args:
            claim: The claim to find evidence for
            context: Workflow context (unused by web search)

        Returns:
            List of Evidence objects from web sources
        """
        raw_results = await self._gatherer.gather_evidence(
            claim.text, max_results=self._max_results
        )

        evidence = []
        for item in raw_results:
            if "error" in item:
                logger.warning(f"Web search error: {item['error']}")
                continue

            evidence.append(
                Evidence(
                    source=item.get("source", "web"),
                    source_type="web",
                    content=item.get("content", "")[:1500],
                    relevance_score=item.get("relevance", 0.6),
                    supports_claim=None,
                )
            )

        return evidence
