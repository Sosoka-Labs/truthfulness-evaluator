"""Workflow configuration types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..protocols import ClaimExtractor, ClaimVerifier, EvidenceGatherer, ReportFormatter


@dataclass(frozen=True)
class WorkflowConfig:
    """Immutable configuration for a truthfulness evaluation workflow.

    Bundles strategy selections with their configuration.
    """

    name: str
    description: str

    # Strategy selections (must implement the relevant protocol)
    extractor: type[ClaimExtractor]
    gatherers: list[type[EvidenceGatherer]]
    verifier: type[ClaimVerifier]
    formatters: list[type[ReportFormatter]]

    # Strategy-specific configuration
    extractor_config: dict[str, Any] = field(default_factory=dict)
    gatherer_configs: list[dict[str, Any]] = field(default_factory=list)
    verifier_config: dict[str, Any] = field(default_factory=dict)
    formatter_configs: list[dict[str, Any]] = field(default_factory=list)

    # Workflow-level configuration
    max_claims: int | None = None
    enable_human_review: bool = False
    human_review_threshold: float = 0.6
