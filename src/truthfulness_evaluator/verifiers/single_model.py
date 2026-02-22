"""Single-model verification adapter."""

from ..chains.verification import VerificationChain
from ..core.logging_config import get_logger
from ..models import Claim, Evidence, VerificationResult

logger = get_logger()


class SingleModelVerifier:
    """Adapter for single-model claim verification using VerificationChain."""

    def __init__(self, model: str = "gpt-4o"):
        self._chain = VerificationChain(model_name=model)

    async def verify(self, claim: Claim, evidence: list[Evidence]) -> VerificationResult:
        """Verify a claim against evidence using a single LLM."""
        return await self._chain.verify(claim, evidence)
