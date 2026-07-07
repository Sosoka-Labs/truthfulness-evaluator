"""Pydantic models for internal verification."""

from typing import Optional

from pydantic import BaseModel, Field


class ClaimClassification(BaseModel):
    """Classification of claim type."""

    claim_type: str = Field(
        description="Type: external_fact, api_signature, version_requirement, configuration, behavioral, or unknown"
    )
    confidence: float = Field(description="Confidence in classification (0.0-1.0)")
    reasoning: str = Field(description="Why this classification")


class InternalVerificationOutput(BaseModel):
    """Output for internal verification."""

    verdict: str = Field(description="SUPPORTS, REFUTES, or NOT_ENOUGH_INFO")
    confidence: float = Field(description="Confidence 0.0-1.0")
    reasoning: str = Field(description="Detailed explanation")
    actual_implementation: Optional[str] = Field(None, description="What was actually found")
    discrepancy: Optional[str] = Field(None, description="Specific discrepancy if any")
