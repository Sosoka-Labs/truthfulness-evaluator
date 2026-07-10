"""Tests for agreement-based consensus aggregation (ConsensusChain).

The per-model verification chains are replaced with fakes returning fixed
``VerificationResult`` objects, so the pure voting/agreement/abstention logic is
verified without any LLM call. The commit/abstain decision and the reported
confidence are driven by inter-model agreement, not self-reported confidence.
"""

from truthfulness_evaluator.llm.chains.consensus import ConsensusChain
from truthfulness_evaluator.models import Claim, Evidence, VerificationResult


def _claim() -> Claim:
    return Claim(id="c1", text="Some claim.", source_document="doc.txt")


class _FakeChain:
    """Stand-in for a VerificationChain with a canned result."""

    def __init__(self, result: VerificationResult):
        self._result = result

    async def verify(self, claim, evidence) -> VerificationResult:
        return self._result


def _result(verdict: str, confidence: float = 0.9, evidence=None) -> VerificationResult:
    return VerificationResult(
        claim_id="c1",
        verdict=verdict,
        confidence=confidence,
        evidence=evidence or [],
        explanation="",
        model_votes={},
    )


def _consensus(votes, *, weights=None, threshold=0.7) -> ConsensusChain:
    """Build a ConsensusChain whose chains return the given per-model verdicts."""
    models = [f"m{i}" for i in range(len(votes))]
    chain = ConsensusChain(models, weights=weights, confidence_threshold=threshold)
    chain._chains = [_FakeChain(_result(v)) for v in votes]
    return chain


class TestAgreement:
    async def test_unanimous_commits_with_full_confidence(self):
        result = await _consensus(["SUPPORTS", "SUPPORTS", "SUPPORTS"]).verify(_claim(), [])
        assert result.verdict == "SUPPORTS"
        assert result.confidence == 1.0

    async def test_confidence_equals_weighted_agreement(self):
        # 2 of 3 agree -> 0.667 agreement; commit at a permissive threshold.
        result = await _consensus(["SUPPORTS", "SUPPORTS", "REFUTES"], threshold=0.5).verify(
            _claim(), []
        )
        assert result.verdict == "SUPPORTS"
        assert round(result.confidence, 2) == 0.67

    async def test_agreement_below_threshold_abstains(self):
        # 2/3 = 0.667 < default 0.7 -> abstain.
        result = await _consensus(["SUPPORTS", "SUPPORTS", "REFUTES"]).verify(_claim(), [])
        assert result.verdict == "NOT_ENOUGH_INFO"

    async def test_tie_abstains(self):
        result = await _consensus(["SUPPORTS", "REFUTES"]).verify(_claim(), [])
        assert result.verdict == "NOT_ENOUGH_INFO"

    async def test_three_way_split_abstains(self):
        result = await _consensus(["SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO"]).verify(_claim(), [])
        assert result.verdict == "NOT_ENOUGH_INFO"

    async def test_unanimous_not_enough_info_is_committed_not_flagged(self):
        result = await _consensus(["NOT_ENOUGH_INFO", "NOT_ENOUGH_INFO"]).verify(_claim(), [])
        assert result.verdict == "NOT_ENOUGH_INFO"
        assert result.confidence == 1.0
        assert "Abstained" not in result.explanation


class TestWeighting:
    async def test_heavier_model_carries_the_vote(self):
        chain = _consensus(["SUPPORTS", "REFUTES"], weights={"m0": 0.7, "m1": 0.3}, threshold=0.7)
        result = await chain.verify(_claim(), [])
        assert result.verdict == "SUPPORTS"
        assert result.model_votes == {"m0": "SUPPORTS", "m1": "REFUTES"}

    async def test_low_self_reported_confidence_does_not_force_abstention(self):
        # Both models agree but report low confidence; agreement (1.0) governs.
        models = ["m0", "m1"]
        chain = ConsensusChain(models, confidence_threshold=0.7)
        chain._chains = [_FakeChain(_result("SUPPORTS", 0.2)) for _ in models]
        result = await chain.verify(_claim(), [])
        assert result.verdict == "SUPPORTS"
        assert result.confidence == 1.0


class TestEvidence:
    async def test_evidence_combined_and_capped_at_five(self):
        many = [
            Evidence(source=f"s{n}", source_type="web", content="x", relevance_score=0.9)
            for n in range(6)
        ]
        models = ["m0", "m1"]
        chain = ConsensusChain(models)
        chain._chains = [
            _FakeChain(_result("SUPPORTS", evidence=many)),
            _FakeChain(_result("SUPPORTS", evidence=[])),
        ]
        result = await chain.verify(_claim(), [])
        assert len(result.evidence) == 5
