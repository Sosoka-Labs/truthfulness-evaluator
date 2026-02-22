"""Claim model for truthfulness evaluation."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Claim(BaseModel):
    """A factual claim extracted from text."""

    id: str = Field(description="Unique claim identifier")
    text: str = Field(description="The claim text")
    source_document: str = Field(description="Source document path/URL")
    source_span: Optional[tuple[int, int]] = Field(
        default=None, description="Character span in source (start, end)"
    )
    context: Optional[str] = Field(default=None, description="Surrounding context for the claim")
    claim_type: Literal["explicit", "implicit", "inferred"] = Field(
        default="explicit", description="Type of claim"
    )

    def __str__(self) -> str:
        return f"Claim({self.id}): {self.text[:80]}..."
