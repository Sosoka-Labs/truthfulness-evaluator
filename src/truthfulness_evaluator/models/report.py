"""Report models for truthfulness evaluation."""

from typing import Optional

from pydantic import BaseModel, Field

from .claim import Claim
from .verification import VerificationResult


class TruthfulnessStatistics(BaseModel):
    """Statistics for a truthfulness evaluation (pure data container).

    Use calculate_statistics() from core.grading to compute these values.
    """

    total_claims: int = Field(default=0)
    supported: int = Field(default=0)
    refuted: int = Field(default=0)
    not_enough_info: int = Field(default=0)
    unverifiable: int = Field(default=0)
    verification_rate: float = Field(default=0.0)
    accuracy_score: float = Field(default=0.0)


class TruthfulnessReport(BaseModel):
    """Final evaluation report (pure data container).

    Use build_report() from core.grading to construct reports with computed fields.
    """

    source_document: str = Field(description="Path/URL of source document")
    overall_grade: Optional[str] = Field(
        default=None,
        pattern=r"^[A-F][+-]?$",
        description="Letter grade (A+ to F)"
    )
    overall_confidence: float = Field(
        default=0.0,
        ge=0.0, le=1.0,
        description="Overall confidence in the evaluation"
    )
    summary: str = Field(
        default="",
        description="Executive summary of findings"
    )
    claims: list[Claim] = Field(default_factory=list)
    verifications: list[VerificationResult] = Field(default_factory=list)
    unvalidated_claims: list[Claim] = Field(
        default_factory=list,
        description="Claims that could not be validated"
    )
    statistics: TruthfulnessStatistics = Field(
        default_factory=TruthfulnessStatistics
    )
