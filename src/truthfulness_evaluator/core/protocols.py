"""Core protocol definitions for the pluggable workflow architecture."""

from typing import Any, Protocol, runtime_checkable

from ..models import Claim, Evidence, TruthfulnessReport, VerificationResult

__all__ = [
    "ClaimExtractor",
    "EvidenceGatherer",
    "ClaimVerifier",
    "ReportFormatter",
]


@runtime_checkable
class ClaimExtractor(Protocol):
    """Protocol for claim extraction strategies.

    Implementations extract factual claims from document text.
    Different implementations handle different document types and domains.
    """

    async def extract(
        self,
        document: str,
        source_path: str,
        *,
        max_claims: int | None = None,
    ) -> list[Claim]:
        """Extract claims from document text.

        Args:
            document: The document text to analyze.
            source_path: Path or URL of the source document.
            max_claims: Optional limit on number of claims to extract.

        Returns:
            List of extracted Claim objects.
        """
        ...


@runtime_checkable
class EvidenceGatherer(Protocol):
    """Protocol for evidence gathering strategies.

    Implementations search for evidence that supports or refutes claims.
    Different implementations search different sources (web, filesystem,
    API endpoints, git history, etc.).
    """

    async def gather(
        self,
        claim: Claim,
        context: dict[str, Any],
    ) -> list[Evidence]:
        """Gather evidence for a claim.

        Args:
            claim: The claim to find evidence for.
            context: Workflow context (root_path, config, etc.).

        Returns:
            List of Evidence objects found.
        """
        ...


@runtime_checkable
class ClaimVerifier(Protocol):
    """Protocol for claim verification strategies.

    Implementations judge whether evidence supports, refutes,
    or is insufficient for a claim. Different implementations use
    different judgment methods (single LLM, consensus, deterministic).
    """

    async def verify(
        self,
        claim: Claim,
        evidence: list[Evidence],
    ) -> VerificationResult:
        """Verify a claim against gathered evidence.

        Args:
            claim: The claim to verify.
            evidence: Evidence gathered for this claim.

        Returns:
            VerificationResult with verdict, confidence, and explanation.
        """
        ...


@runtime_checkable
class ReportFormatter(Protocol):
    """Protocol for report formatting strategies.

    Implementations produce output in different formats
    (JSON, Markdown, HTML, custom domain-specific formats).
    """

    def format(self, report: TruthfulnessReport) -> str:
        """Format a truthfulness report.

        Args:
            report: The report to format.

        Returns:
            Formatted report as a string.
        """
        ...

    def file_extension(self) -> str:
        """Return the default file extension for this format.

        Returns:
            Extension string (e.g., ".json", ".md", ".html").
        """
        ...
