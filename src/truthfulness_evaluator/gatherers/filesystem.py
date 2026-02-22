"""Filesystem evidence gatherer adapter."""

from typing import Any

from ..core.logging_config import get_logger
from ..evidence.agent import FilesystemEvidenceAgent
from ..models import Claim, Evidence

logger = get_logger()


class FilesystemGatherer:
    """Adapter wrapping FilesystemEvidenceAgent for the EvidenceGatherer protocol."""

    def __init__(self, model: str = "gpt-4o"):
        """Initialize filesystem gatherer.

        Args:
            model: LLM model name for ReAct agent
        """
        self._model = model

    async def gather(self, claim: Claim, context: dict[str, Any]) -> list[Evidence]:
        """Gather filesystem evidence for a claim.

        Args:
            claim: The claim to find evidence for
            context: Workflow context containing root_path

        Returns:
            List of Evidence objects from filesystem sources
        """
        root_path = context.get("root_path")
        if not root_path:
            logger.warning("No root_path in context, skipping filesystem search")
            return []

        agent = FilesystemEvidenceAgent(root_path=root_path, model=self._model)
        raw_results = await agent.search(claim.text)

        evidence = []
        for item in raw_results:
            evidence.append(
                Evidence(
                    source=item.get("file_path", "unknown"),
                    source_type="filesystem",
                    content=item.get("content", "")[:1000],
                    relevance_score=item.get("relevance", 0.5),
                    supports_claim=item.get("supports"),
                )
            )

        return evidence
