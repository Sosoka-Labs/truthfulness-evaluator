"""Verification chains using structured outputs."""

from truthfulness_evaluator.llm.factory import create_chat_model
from truthfulness_evaluator.llm.models import VerificationOutput
from truthfulness_evaluator.llm.prompts.verification import VERIFICATION_PROMPT
from truthfulness_evaluator.models import Claim, Evidence, VerificationResult


class VerificationChain:
    """Single-model verification chain with structured outputs."""

    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self._llm = None

    @property
    def llm(self):
        """Lazy initialization of LLM with structured output."""
        if self._llm is None:
            base_llm = create_chat_model(self.model_name, temperature=0)
            # Use structured output
            self._llm = base_llm.with_structured_output(VerificationOutput)
        return self._llm

    async def verify(self, claim: Claim, evidence: list[Evidence]) -> VerificationResult:
        """Verify a claim against evidence using structured output."""

        # Build evidence text with relevance indicators
        if evidence:
            evidence_parts = []
            for i, e in enumerate(evidence[:4], 1):  # Top 4 evidence items
                support_indicator = ""
                if e.supports_claim is True:
                    support_indicator = "[SUPPORTS]"
                elif e.supports_claim is False:
                    support_indicator = "[REFUTES]"
                else:
                    support_indicator = "[NEUTRAL]"

                evidence_parts.append(
                    f"\n--- Evidence {i} ({e.source_type}) {support_indicator} ---\n"
                    f"Source: {e.source}\n"
                    f"Relevance: {e.relevance_score:.0%}\n"
                    f"Content: {e.content[:600]}"
                )

            evidence_text = "\n".join(evidence_parts)
        else:
            evidence_text = "No evidence provided."

        chain = VERIFICATION_PROMPT | self.llm

        try:
            result: VerificationOutput = await chain.ainvoke(
                {"claim": claim.text, "evidence": evidence_text}
            )

            # Normalize verdict
            verdict = result.verdict.upper()
            if verdict not in ["SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO"]:
                verdict = "NOT_ENOUGH_INFO"

            # Combine reasoning with key evidence
            full_explanation = result.reasoning
            if result.key_evidence:
                full_explanation += f"\n\nKey evidence: {result.key_evidence}"

            # Adjust confidence based on evidence quality
            confidence = max(0.0, min(1.0, result.confidence))
            if not evidence:
                confidence = min(confidence, 0.3)

            return VerificationResult(
                claim_id=claim.id,
                verdict=verdict,
                confidence=confidence,
                evidence=evidence,
                explanation=full_explanation,
                model_votes={self.model_name: verdict},
            )

        except Exception as e:
            # Fallback result on error
            return VerificationResult(
                claim_id=claim.id,
                verdict="NOT_ENOUGH_INFO",
                confidence=0.0,
                evidence=evidence,
                explanation=f"Verification failed: {str(e)}",
                model_votes={self.model_name: "NOT_ENOUGH_INFO"},
            )
