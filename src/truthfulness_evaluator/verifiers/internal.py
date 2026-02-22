"""Internal/codebase verification adapter."""

from ..chains.internal_verification import ClaimClassifier, InternalVerificationChain
from ..core.logging_config import get_logger
from ..models import Claim, Evidence, VerificationResult

logger = get_logger()


class InternalVerifier:
    """Adapter for internal/codebase verification using InternalVerificationChain."""

    def __init__(
        self,
        root_path: str,
        *,
        model: str = "gpt-4o",
        classification_model: str = "gpt-4o-mini",
    ):
        self._chain = InternalVerificationChain(root_path=root_path, model=model)
        self._classifier = ClaimClassifier(model=classification_model)

    async def verify(self, claim: Claim, evidence: list[Evidence]) -> VerificationResult:
        """Verify a claim against the codebase after classifying it."""
        try:
            classification = await self._classifier.classify(claim)

            if classification.claim_type in ("external_fact", "unknown"):
                return VerificationResult(
                    claim_id=claim.id,
                    verdict="NOT_ENOUGH_INFO",
                    confidence=0.0,
                    evidence=[],
                    explanation=(
                        f"Claim classified as '{classification.claim_type}' -- "
                        "not suitable for internal verification."
                    ),
                    model_votes={},
                )

            return await self._chain.verify(claim, classification)

        except Exception as e:
            logger.warning(f"Classification failed for claim {claim.id}: {e}")
            return VerificationResult(
                claim_id=claim.id,
                verdict="NOT_ENOUGH_INFO",
                confidence=0.0,
                evidence=[],
                explanation=f"Classification error: {str(e)}",
                model_votes={},
            )
