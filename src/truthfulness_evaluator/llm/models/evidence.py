"""Pydantic models for evidence analysis."""

from typing import List, Optional

from pydantic import BaseModel, Field


class EvidenceAnalysisItem(BaseModel):
    """Analysis of a single evidence item."""

    index: int = Field(description="Index of the evidence item")
    relevance: float = Field(description="Relevance score from 0.0 to 1.0")
    supports: Optional[bool] = Field(
        None, description="True if supports, False if refutes, null if neutral"
    )
    credibility: float = Field(description="Credibility score from 0.0 to 1.0")
    reasoning: str = Field(description="Brief reasoning for the assessment")


class EvidenceAnalysisOutput(BaseModel):
    """Structured output for evidence analysis."""

    evidence_analysis: List[EvidenceAnalysisItem] = Field(
        description="Analysis of each evidence item"
    )
    summary: str = Field(description="Overall summary of evidence quality")
