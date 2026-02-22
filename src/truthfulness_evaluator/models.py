"""Pydantic models for truthfulness evaluation."""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, computed_field

# Type definitions
Verdict = Literal["SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO", "UNVERIFIABLE"]


class Claim(BaseModel):
    """A factual claim extracted from text."""
    
    id: str = Field(description="Unique claim identifier")
    text: str = Field(description="The claim text")
    source_document: str = Field(description="Source document path/URL")
    source_span: Optional[tuple[int, int]] = Field(
        default=None, description="Character span in source (start, end)"
    )
    context: Optional[str] = Field(
        default=None, description="Surrounding context for the claim"
    )
    claim_type: Literal["explicit", "implicit", "inferred"] = Field(
        default="explicit",
        description="Type of claim"
    )
    
    def __str__(self) -> str:
        return f"Claim({self.id}): {self.text[:80]}..."


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


class VerificationResult(BaseModel):
    """Result of verifying a single claim."""
    
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
    
    @computed_field
    @property
    def is_verified(self) -> bool:
        """Whether this claim has been verified with high confidence."""
        return self.verdict in ["SUPPORTS", "REFUTES"] and self.confidence >= 0.7


class TruthfulnessStatistics(BaseModel):
    """Statistics for a truthfulness evaluation."""
    
    total_claims: int = Field(default=0)
    supported: int = Field(default=0)
    refuted: int = Field(default=0)
    not_enough_info: int = Field(default=0)
    unverifiable: int = Field(default=0)
    
    @computed_field
    @property
    def verification_rate(self) -> float:
        """Percentage of claims that were verified (SUPPORTS or REFUTES)."""
        if self.total_claims == 0:
            return 0.0
        return (self.supported + self.refuted) / self.total_claims
    
    @computed_field
    @property
    def accuracy_score(self) -> float:
        """Simple accuracy score based on supported vs refuted."""
        verified = self.supported + self.refuted
        if verified == 0:
            return 0.0
        return self.supported / verified


class TruthfulnessReport(BaseModel):
    """Final evaluation report."""
    
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
    
    def calculate_grade(self) -> str:
        """Calculate letter grade from verification results."""
        if not self.verifications:
            return "F"
        
        verified = [v for v in self.verifications if v.is_verified]
        if not verified:
            return "F"
        
        support_ratio = sum(1 for v in verified if v.verdict == "SUPPORTS") / len(verified)
        confidence = sum(v.confidence for v in verified) / len(verified)
        
        # Grade calculation
        score = support_ratio * confidence
        
        if score >= 0.9:
            return "A+"
        elif score >= 0.85:
            return "A"
        elif score >= 0.8:
            return "A-"
        elif score >= 0.75:
            return "B+"
        elif score >= 0.7:
            return "B"
        elif score >= 0.65:
            return "B-"
        elif score >= 0.6:
            return "C+"
        elif score >= 0.55:
            return "C"
        elif score >= 0.5:
            return "C-"
        elif score >= 0.4:
            return "D"
        else:
            return "F"
    
    def model_post_init(self, __context: Any) -> None:
        """Calculate derived fields after initialization."""
        if not self.overall_grade:
            self.overall_grade = self.calculate_grade()
        
        # Calculate statistics
        self.statistics = TruthfulnessStatistics(
            total_claims=len(self.claims),
            supported=sum(1 for v in self.verifications if v.verdict == "SUPPORTS"),
            refuted=sum(1 for v in self.verifications if v.verdict == "REFUTES"),
            not_enough_info=sum(1 for v in self.verifications if v.verdict == "NOT_ENOUGH_INFO"),
            unverifiable=sum(1 for v in self.verifications if v.verdict == "UNVERIFIABLE"),
        )
        
        # Calculate overall confidence
        if self.verifications:
            self.overall_confidence = sum(v.confidence for v in self.verifications) / len(self.verifications)
        
        # Generate summary if not provided
        if not self.summary:
            self.summary = self._generate_summary()
    
    def _generate_summary(self) -> str:
        """Generate automatic summary."""
        stats = self.statistics
        grade = self.overall_grade or self.calculate_grade()
        
        if stats.total_claims == 0:
            return "No claims were extracted from the document."
        
        summary = f"Document received grade {grade}. "
        summary += f"Of {stats.total_claims} claims, "
        summary += f"{stats.supported} were supported, "
        summary += f"{stats.refuted} were refuted, and "
        summary += f"{stats.not_enough_info + stats.unverifiable} could not be verified."
        
        if stats.verification_rate < 0.5:
            summary += " Many claims lacked sufficient evidence for verification."
        elif stats.accuracy_score < 0.7:
            summary += " Several claims were found to be inaccurate."
        else:
            summary += " The document appears to be largely accurate."
        
        return summary
