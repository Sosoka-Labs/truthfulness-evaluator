"""Consensus chain for multi-model verification.

Design rationale (see ``llm_memory/research-multimodel-voting.md``): heterogeneous
LLMs make correlated errors and their self-reported confidence is systematically
overconfident and poorly calibrated. So both the commit/abstain decision and the
reported confidence are driven by *inter-model agreement*, not by the models'
own confidence scores. The ensemble abstains (``NOT_ENOUGH_INFO``) on a tie for
the lead, or when weighted agreement for the leading verdict is below
``confidence_threshold`` — trading yield for precision on the 3-way verdict.
"""

import asyncio
from collections import Counter

from ...core.logging_config import get_logger
from ...models import Claim, Evidence, VerificationResult
from .verification import VerificationChain

logger = get_logger()

ABSTAIN = "NOT_ENOUGH_INFO"


class ConsensusChain:
    """Multi-model consensus via weighted, agreement-based voting."""

    def __init__(
        self,
        model_names: list[str],
        weights: dict[str, float] | None = None,
        confidence_threshold: float = 0.7,
    ):
        self.model_names = model_names
        self.weights = weights or {m: 1.0 / len(model_names) for m in model_names}
        # Minimum weighted agreement for the leading verdict to be committed;
        # below it (or on a tie) the ensemble abstains. With N equal-weight
        # models a value of 0.7 effectively requires near-unanimity (e.g. 3
        # models must all agree, since 2/3 = 0.67 < 0.7); lower it to accept
        # simple majorities.
        self.confidence_threshold = confidence_threshold
        self._chains: list[VerificationChain] | None = None

    @property
    def chains(self) -> list[VerificationChain]:
        """Lazy initialization of the per-model verification chains."""
        if self._chains is None:
            self._chains = [VerificationChain(m) for m in self.model_names]
        return self._chains

    async def verify(self, claim: Claim, evidence: list[Evidence]) -> VerificationResult:
        """Verify a claim by polling every model and aggregating by agreement."""
        results = await asyncio.gather(*[chain.verify(claim, evidence) for chain in self.chains])

        votes = {self.model_names[i]: r.verdict for i, r in enumerate(results)}
        self_reported = {self.model_names[i]: r.confidence for i, r in enumerate(results)}

        # Weighted tally of verdicts.
        tally: Counter = Counter()
        for model, verdict in votes.items():
            tally[verdict] += self.weights.get(model, 1.0 / len(self.model_names))

        total_weight = sum(tally.values()) or 1.0
        ranked = tally.most_common()
        leading_verdict, leading_weight = ranked[0]
        agreement = leading_weight / total_weight

        # A shared top weight is unresolved agreement -> abstain.
        tie = len(ranked) > 1 and ranked[1][1] == leading_weight
        abstained = tie or agreement < self.confidence_threshold
        final_verdict = ABSTAIN if abstained else leading_verdict

        # Confidence reflects consensus strength, not the models' unreliable
        # self-reported scores.
        confidence = round(agreement, 4)

        all_evidence: list[Evidence] = []
        for r in results:
            all_evidence.extend(r.evidence)

        vote_lines = [
            f"{m}: {votes[m]} (self-reported {self_reported[m]:.0%})" for m in self.model_names
        ]
        explanation_parts = [
            f"Consensus: {final_verdict} ({agreement:.0%} weighted agreement)",
            "Model votes:",
            *vote_lines,
        ]
        if final_verdict == ABSTAIN and leading_verdict != ABSTAIN:
            reason = "tie" if tie else f"agreement below {self.confidence_threshold:.0%} threshold"
            explanation_parts.append(f"(Abstained: {reason}.)")

        logger.debug(
            "Consensus %s at %.0f%% agreement; votes=%s", final_verdict, agreement * 100, votes
        )

        return VerificationResult(
            claim_id=claim.id,
            verdict=final_verdict,
            confidence=confidence,
            evidence=all_evidence[:5],
            explanation="\n".join(explanation_parts),
            model_votes=votes,
        )
