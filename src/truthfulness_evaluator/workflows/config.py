"""Workflow configuration types."""

from __future__ import annotations

from dataclasses import dataclass

from ..protocols import ClaimExtractor, ClaimVerifier, EvidenceGatherer, ReportFormatter


@dataclass
class WorkflowConfig:
    """Configuration for a truthfulness evaluation workflow.

    Bundles ready-to-use strategy instances with workflow-level settings.
    Callers construct strategy instances with desired config, then hand
    them to WorkflowConfig. The builder plugs them into graph nodes.
    """

    name: str
    description: str

    # Strategy instances (must satisfy the relevant protocol)
    extractor: ClaimExtractor
    gatherers: list[EvidenceGatherer]
    verifier: ClaimVerifier
    formatters: list[ReportFormatter]

    # Workflow-level configuration
    max_claims: int | None = None
    enable_human_review: bool = False
    human_review_threshold: float = 0.6
