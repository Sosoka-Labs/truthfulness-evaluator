"""Unified state schema for all workflow types."""

from typing import Any
from typing_extensions import TypedDict

from ..models import Claim, Evidence, TruthfulnessReport, VerificationResult


class WorkflowState(TypedDict):
    """Unified state for all truthfulness evaluation workflows.

    The core fields are used by every workflow. The `extensions` field
    provides a namespace for strategy-specific state (e.g., claim
    classifications for internal verification workflows).
    """

    # Input
    document: str
    document_path: str

    # Core pipeline state
    claims: list[Claim]
    current_claim_index: int
    evidence_cache: dict[str, list[Evidence]]
    verifications: list[VerificationResult]

    # Output
    final_report: TruthfulnessReport | None

    # Strategy-specific state (open for extension, closed for modification)
    extensions: dict[str, Any]
