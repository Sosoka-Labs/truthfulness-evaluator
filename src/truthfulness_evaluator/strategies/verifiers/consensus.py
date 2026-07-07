"""Multi-model consensus verification adapter."""

from truthfulness_evaluator.core.logging_config import get_logger
from truthfulness_evaluator.llm.chains.consensus import ConsensusChain
from truthfulness_evaluator.models import Claim, Evidence, VerificationResult

logger = get_logger()


class ConsensusVerifier:
    """Adapter for multi-model consensus verification using ConsensusChain."""

    def __init__(
        self,
        models: list[str],
        *,
        weights: dict[str, float] | None = None,
        confidence_threshold: float = 0.7,
    ):
        self._chain = ConsensusChain(
            model_names=models,
            weights=weights,
            confidence_threshold=confidence_threshold,
        )

    async def verify(self, claim: Claim, evidence: list[Evidence]) -> VerificationResult:
        """Verify a claim using multi-model consensus."""
        return await self._chain.verify(claim, evidence)
