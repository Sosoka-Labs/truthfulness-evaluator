"""Evidence model for truthfulness evaluation."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Evidence found for or against a claim."""

    source: str = Field(description="Evidence source (URL, file path)")
    source_type: Literal["web", "filesystem", "knowledge_base"] = Field(
        description="Type of evidence source"
    )
    content: str = Field(description="Relevant content snippet")
    relevance_score: float = Field(
        ge=0.0, le=1.0,
        description="Relevance score (0-1)"
    )
    supports_claim: Optional[bool] = Field(
        default=None,
        description="Whether this supports (True), refutes (False), or is neutral (None)"
    )
    credibility_score: float = Field(
        default=0.5,
        ge=0.0, le=1.0,
        description="Source credibility score (0-1)"
    )
