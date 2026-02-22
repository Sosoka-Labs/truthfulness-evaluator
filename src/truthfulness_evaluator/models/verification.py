"""Verification result model for truthfulness evaluation."""

from pydantic import BaseModel, Field

from .types import Verdict
from .evidence import Evidence


class VerificationResult(BaseModel):
    """Result of verifying a single claim (pure data container)."""

    claim_id: str = Field(description="ID of the claim being verified")
    verdict: Verdict = Field(description="Verification verdict")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in the verdict (0-1)"
    )
    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Evidence supporting the verdict"
    )
    explanation: str = Field(
        description="Human-readable explanation of the verdict"
    )
    model_votes: dict[str, Verdict] = Field(
        default_factory=dict,
        description="Individual model votes (model_name -> verdict)"
    )
