"""Tests for consensus aggregation (ConsensusChain / ICEConsensusChain).

The per-model verification chains are replaced with fakes returning fixed
``VerificationResult`` objects, so the pure voting/threshold/aggregation logic
is verified without any LLM call.
"""

from truthfulness_evaluator.llm.chains.consensus import ConsensusChain, ICEConsensusChain
from truthfulness_evaluator.models import Claim, Evidence, VerificationResult


def _claim() -> Claim:
    return Claim(id="c1", text="Some claim.", source_document="doc.txt")


class _FakeChain:
    """Stand-in for a VerificationChain with a canned result."""

    def __init__(self, result: VerificationResult):
        self._result = result

    async def verify(self, claim, evidence) -> VerificationResult:
        return self._result


def _result(verdict: str, confidence: float, evidence=None) -> VerificationResult:
    return VerificationResult(
        claim_id="c1",
        verdict=verdict,
        confidence=confidence,
        evidence=evidence or [],
        explanation="",
        model_votes={},
    )


class TestConsensusChain:
    async def test_weighted_vote_favours_heavier_model(self):
        chain = ConsensusChain(["m1", "m2"], weights={"m1": 0.7, "m2": 0.3})
        chain._chains = [
            _FakeChain(_result("SUPPORTS", 0.9)),
            _FakeChain(_result("REFUTES", 0.8)),
        ]
        result = await chain.verify(_claim(), [])
        assert result.verdict == "SUPPORTS"
        assert result.model_votes == {"m1": "SUPPORTS", "m2": "REFUTES"}

    async def test_low_average_confidence_forces_nei(self):
        chain = ConsensusChain(["m1", "m2"], confidence_threshold=0.7)
        chain._chains = [
            _FakeChain(_result("SUPPORTS", 0.5)),
            _FakeChain(_result("SUPPORTS", 0.5)),
        ]
        result = await chain.verify(_claim(), [])
        assert result.verdict == "NOT_ENOUGH_INFO"

    async def test_evidence_combined_and_capped_at_five(self):
        many = [
            Evidence(source=f"s{n}", source_type="web", content="x", relevance_score=0.9)
            for n in range(6)
        ]
        chain = ConsensusChain(["m1", "m2"])
        chain._chains = [
            _FakeChain(_result("SUPPORTS", 0.9, evidence=many)),
            _FakeChain(_result("SUPPORTS", 0.9, evidence=[])),
        ]
        result = await chain.verify(_claim(), [])
        assert len(result.evidence) == 5

    async def test_average_confidence_reported(self):
        chain = ConsensusChain(["m1", "m2"])
        chain._chains = [
            _FakeChain(_result("SUPPORTS", 0.8)),
            _FakeChain(_result("SUPPORTS", 1.0)),
        ]
        result = await chain.verify(_claim(), [])
        assert result.confidence == 0.9


class TestICEConsensusChain:
    def test_consensus_reached_when_all_agree(self):
        ice = ICEConsensusChain(["m1", "m2"])
        assert ice._consensus_reached({"m1": "SUPPORTS", "m2": "SUPPORTS"}) is True

    def test_consensus_not_reached_when_split(self):
        ice = ICEConsensusChain(["m1", "m2"])
        assert ice._consensus_reached({"m1": "SUPPORTS", "m2": "REFUTES"}) is False

    async def test_unanimous_agreement_short_circuits_rounds(self):
        ice = ICEConsensusChain(["m1", "m2"], max_rounds=3)
        ice._chains = [
            _FakeChain(_result("SUPPORTS", 0.9)),
            _FakeChain(_result("SUPPORTS", 0.9)),
        ]
        result = await ice.verify(_claim(), [])
        assert result.verdict == "SUPPORTS"
        assert result.model_votes == {"m1": "SUPPORTS", "m2": "SUPPORTS"}

    async def test_low_confidence_forces_nei(self):
        ice = ICEConsensusChain(["m1", "m2"], max_rounds=1, confidence_threshold=0.7)
        ice._chains = [
            _FakeChain(_result("SUPPORTS", 0.4)),
            _FakeChain(_result("SUPPORTS", 0.4)),
        ]
        result = await ice.verify(_claim(), [])
        assert result.verdict == "NOT_ENOUGH_INFO"
