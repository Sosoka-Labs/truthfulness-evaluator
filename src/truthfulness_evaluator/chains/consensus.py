"""Consensus chains for multi-model verification."""

import asyncio
from collections import Counter

from ..models import Claim, Evidence, VerificationResult, Verdict
from .verification import VerificationChain
from ..logging_config import get_logger

logger = get_logger()


class ConsensusChain:
    """Multi-model consensus with weighted voting."""
    
    def __init__(
        self,
        model_names: list[str],
        weights: dict[str, float] | None = None,
        confidence_threshold: float = 0.7
    ):
        self.model_names = model_names
        self.weights = weights or {m: 1.0 / len(model_names) for m in model_names}
        self.confidence_threshold = confidence_threshold
        self._chains = None
    
    @property
    def chains(self) -> list[VerificationChain]:
        """Lazy initialization of verification chains."""
        if self._chains is None:
            self._chains = [VerificationChain(m) for m in self.model_names]
        return self._chains
    
    async def verify(self, claim: Claim, evidence: list[Evidence]) -> VerificationResult:
        """Verify claim using multi-model consensus."""
        # Get votes from all models in parallel
        results = await asyncio.gather(*[
            chain.verify(claim, evidence)
            for chain in self.chains
        ])
        
        # Collect votes and confidences
        votes = {}
        confidences = {}
        explanations = []
        
        for i, result in enumerate(results):
            model = self.model_names[i]
            votes[model] = result.verdict
            confidences[model] = result.confidence
            explanations.append(f"{model}: {result.verdict} (confidence: {result.confidence:.2f})")
        
        # Weighted voting
        weighted_votes = Counter()
        for model, verdict in votes.items():
            weight = self.weights.get(model, 1.0 / len(self.model_names))
            weighted_votes[verdict] += weight
        
        # Get winning verdict
        final_verdict = weighted_votes.most_common(1)[0][0]
        
        # Calculate overall confidence
        avg_confidence = sum(confidences.values()) / len(confidences)
        
        # If confidence too low, mark as NEI
        if avg_confidence < self.confidence_threshold:
            final_verdict = "NOT_ENOUGH_INFO"

        # Debug: show all votes
        vote_str = ", ".join([f"{m}: {v}" for m, v in votes.items()])
        logger.debug(f"Model votes: {vote_str}")

        # Combine evidence from all results
        all_evidence = []
        for r in results:
            all_evidence.extend(r.evidence)
        
        return VerificationResult(
            claim_id=claim.id,
            verdict=final_verdict,
            confidence=avg_confidence,
            evidence=all_evidence[:5],  # Deduplicate and limit
            explanation="\n".join([
                f"Consensus: {final_verdict}",
                "Model votes:",
                *explanations
            ]),
            model_votes=votes
        )


class ICEConsensusChain:
    """Iterative Consensus Ensemble - models critique each other."""
    
    def __init__(
        self,
        model_names: list[str],
        max_rounds: int = 3,
        confidence_threshold: float = 0.7
    ):
        self.model_names = model_names
        self.max_rounds = max_rounds
        self.confidence_threshold = confidence_threshold
        self._chains = None
    
    @property
    def chains(self) -> list[VerificationChain]:
        """Lazy initialization of verification chains."""
        if self._chains is None:
            self._chains = [VerificationChain(m) for m in self.model_names]
        return self._chains
    
    async def verify(self, claim: Claim, evidence: list[Evidence]) -> VerificationResult:
        """Verify claim using ICE (Iterative Consensus Ensemble)."""
        
        # Round 1: Initial votes
        results = await asyncio.gather(*[
            chain.verify(claim, evidence)
            for chain in self.chains
        ])
        
        votes = {self.model_names[i]: r.verdict for i, r in enumerate(results)}
        
        # Rounds 2-N: Critique and revise
        for round_num in range(2, self.max_rounds + 1):
            if self._consensus_reached(votes):
                break
            
            # Models critique each other's reasoning
            critiques = await self._gather_critiques(claim, evidence, votes, round_num)
            
            # Revise votes based on critiques
            new_results = await asyncio.gather(*[
                self._revise_vote(chain, claim, evidence, votes, critiques, round_num)
                for chain in self.chains
            ])
            
            votes = {self.model_names[i]: r.verdict for i, r in enumerate(new_results)}
        
        # Final aggregation
        return self._aggregate_results(claim, votes, results, evidence)
    
    def _consensus_reached(self, votes: dict[str, Verdict]) -> bool:
        """Check if all models agree."""
        return len(set(votes.values())) == 1
    
    async def _gather_critiques(
        self,
        claim: Claim,
        evidence: list[Evidence],
        votes: dict[str, Verdict],
        round_num: int
    ) -> dict[str, str]:
        """Gather critiques from each model about others' reasoning."""
        # Simplified - in full implementation, each model critiques others
        return {model: f"Round {round_num} critique" for model in self.model_names}
    
    async def _revise_vote(
        self,
        chain: VerificationChain,
        claim: Claim,
        evidence: list[Evidence],
        current_votes: dict[str, Verdict],
        critiques: dict[str, str],
        round_num: int
    ) -> VerificationResult:
        """Revise vote based on critiques."""
        # For now, just re-verify (full implementation would incorporate critiques)
        return await chain.verify(claim, evidence)
    
    def _aggregate_results(
        self,
        claim: Claim,
        votes: dict[str, Verdict],
        results: list[VerificationResult],
        evidence: list[Evidence]
    ) -> VerificationResult:
        """Aggregate final results."""
        # Simple majority vote
        vote_counts = Counter(votes.values())
        final_verdict = vote_counts.most_common(1)[0][0]
        
        # Average confidence
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        if avg_confidence < self.confidence_threshold:
            final_verdict = "NOT_ENOUGH_INFO"
        
        return VerificationResult(
            claim_id=claim.id,
            verdict=final_verdict,
            confidence=avg_confidence,
            evidence=evidence,
            explanation=f"ICE Consensus after up to {self.max_rounds} rounds",
            model_votes=votes
        )
