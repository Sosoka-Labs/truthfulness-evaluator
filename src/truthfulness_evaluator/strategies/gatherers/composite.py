"""Composite evidence gatherer for running multiple gatherers in parallel."""

import asyncio
from typing import Any

from ...core.logging_config import get_logger
from ...core.protocols import EvidenceGatherer
from ...models import Claim, Evidence

logger = get_logger()


class CompositeGatherer:
    """Runs multiple evidence gatherers in parallel and combines results."""

    def __init__(
        self,
        gatherers: list[EvidenceGatherer],
        *,
        max_total_evidence: int = 10,
        deduplicate: bool = True,
    ):
        """Initialize composite gatherer.

        Args:
            gatherers: List of gatherer instances to run in parallel
            max_total_evidence: Maximum total evidence items to return
            deduplicate: Whether to remove duplicate evidence by source
        """
        self._gatherers = gatherers
        self._max_total_evidence = max_total_evidence
        self._deduplicate = deduplicate

    async def gather(self, claim: Claim, context: dict[str, Any]) -> list[Evidence]:
        """Gather evidence from all configured gatherers in parallel.

        Args:
            claim: The claim to find evidence for
            context: Workflow context passed to all gatherers

        Returns:
            Combined, deduplicated, and sorted evidence list
        """
        tasks = [gatherer.gather(claim, context) for gatherer in self._gatherers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_evidence: list[Evidence] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Gatherer {self._gatherers[i].__class__.__name__} failed: {result}")
                continue
            all_evidence.extend(result)

        if self._deduplicate:
            all_evidence = self._dedupe(all_evidence)

        all_evidence.sort(key=lambda e: e.relevance_score, reverse=True)

        return all_evidence[: self._max_total_evidence]

    @staticmethod
    def _dedupe(evidence_list: list[Evidence]) -> list[Evidence]:
        """Remove duplicate evidence by source field.

        Args:
            evidence_list: List of evidence items to deduplicate

        Returns:
            Deduplicated list (preserves first occurrence)
        """
        seen = set()
        deduped = []
        for evidence in evidence_list:
            if evidence.source not in seen:
                seen.add(evidence.source)
                deduped.append(evidence)
        return deduped
