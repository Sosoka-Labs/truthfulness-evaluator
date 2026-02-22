"""Evidence processing using structured outputs."""

from typing import List, Optional

from pydantic import BaseModel, Field

from ...models import Claim, Evidence
from ..factory import create_chat_model
from ..prompts.verification import EVIDENCE_ANALYSIS_PROMPT


# Structured output models
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


class EvidenceProcessor:
    """Process and analyze evidence for claims using structured outputs."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self._llm = None

    @property
    def llm(self):
        """Lazy initialization of LLM with structured output."""
        if self._llm is None:
            base_llm = create_chat_model(self.model, temperature=0)
            self._llm = base_llm.with_structured_output(EvidenceAnalysisOutput)
        return self._llm

    async def analyze_evidence(
        self, claim: Claim, evidence_list: list[Evidence]
    ) -> tuple[list[Evidence], str]:
        """
        Analyze evidence and determine which pieces are relevant.

        Returns:
            Tuple of (filtered_evidence, analysis_summary)
        """
        if not evidence_list:
            return [], "No evidence provided"

        # Build evidence text
        evidence_text = "\n\n---\n\n".join(
            [
                f"[{i}] Source: {e.source}\nType: {e.source_type}\nContent: {e.content[:800]}"
                for i, e in enumerate(evidence_list[:5])  # Top 5 pieces
            ]
        )

        chain = EVIDENCE_ANALYSIS_PROMPT | self.llm

        try:
            result: EvidenceAnalysisOutput = await chain.ainvoke(
                {"claim": claim.text, "evidence": evidence_text}
            )

            # Update evidence with analysis
            for analysis in result.evidence_analysis:
                idx = analysis.index
                if 0 <= idx < len(evidence_list):
                    evidence_list[idx].relevance_score = max(0.0, min(1.0, analysis.relevance))
                    evidence_list[idx].supports_claim = analysis.supports
                    evidence_list[idx].credibility_score = max(0.0, min(1.0, analysis.credibility))

            # Sort by relevance
            evidence_list.sort(key=lambda e: e.relevance_score, reverse=True)

            return evidence_list, result.summary

        except Exception as e:
            # If analysis fails, return original evidence
            return evidence_list, f"Analysis failed: {str(e)}"

    async def synthesize_evidence(self, claim: Claim, evidence_list: list[Evidence]) -> str:
        """
        Synthesize multiple pieces of evidence into a coherent summary.

        Returns:
            Summary text
        """
        if not evidence_list:
            return "No evidence available"

        # Filter to high-relevance evidence
        good_evidence = [e for e in evidence_list if e.relevance_score >= 0.5][:3]

        if not good_evidence:
            return "No highly relevant evidence found"

        # Simple synthesis without LLM for speed
        parts = []
        for e in good_evidence:
            support = (
                "supports"
                if e.supports_claim
                else "refutes" if e.supports_claim is False else "is neutral on"
            )
            parts.append(
                f"{e.source} ({e.source_type}) {support} the claim with {e.relevance_score:.0%} relevance"
            )

        return "; ".join(parts)
