"""Pydantic models for verification."""

from typing import Optional

from pydantic import BaseModel, Field


class VerificationOutput(BaseModel):
    """Structured output for claim verification."""

    verdict: str = Field(description="Verdict: SUPPORTS, REFUTES, or NOT_ENOUGH_INFO")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    reasoning: str = Field(description="Detailed explanation of the verdict")
    key_evidence: Optional[str] = Field(None, description="Most important evidence considered")
