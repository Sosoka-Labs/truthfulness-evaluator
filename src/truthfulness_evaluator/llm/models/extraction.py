"""Pydantic models for claim extraction."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ExtractedClaim(BaseModel):
    """A single extracted claim."""

    text: str = Field(description="The claim text")
    claim_type: str = Field(description="Type: explicit, implicit, or inferred")


class ClaimExtractionOutput(BaseModel):
    """Output structure for claim extraction."""

    claims: List[ExtractedClaim] = Field(description="List of extracted claims")


class KnowledgeTriplet(BaseModel):
    """Subject-relation-object triplet."""

    subject: str = Field(description="The subject of the claim")
    relation: str = Field(description="The relationship/action")
    object: str = Field(description="The object/target")
    context: Optional[str] = Field(None, description="Additional context")


class TripletExtractionOutput(BaseModel):
    """Output structure for triplet extraction."""

    triplets: List[KnowledgeTriplet] = Field(description="List of knowledge triplets")
