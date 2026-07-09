"""Tests for EvidenceProcessor.

``synthesize_evidence`` is pure (no LLM) and tested directly.
``analyze_evidence`` has its LLM step replaced with a ``RunnableLambda`` to
verify score clamping, relevance sorting, and the empty-list short circuit.
"""

from langchain_core.runnables import RunnableLambda
from truthfulness_evaluator.llm.chains.evidence import (
    EvidenceAnalysisItem,
    EvidenceAnalysisOutput,
    EvidenceProcessor,
)
from truthfulness_evaluator.models import Claim, Evidence


def _claim() -> Claim:
    return Claim(id="c1", text="Some claim.", source_document="doc.txt")


def _ev(source: str, relevance: float, supports=None) -> Evidence:
    return Evidence(
        source=source,
        source_type="web",
        content="content",
        relevance_score=relevance,
        supports_claim=supports,
    )


class TestSynthesizeEvidence:
    async def test_no_evidence(self):
        assert (
            await EvidenceProcessor().synthesize_evidence(_claim(), []) == "No evidence available"
        )

    async def test_filters_below_relevance_threshold(self):
        evidence = [_ev("weak", 0.4, supports=True), _ev("strong", 0.9, supports=True)]
        summary = await EvidenceProcessor().synthesize_evidence(_claim(), evidence)
        assert "strong" in summary
        assert "weak" not in summary

    async def test_all_low_relevance(self):
        evidence = [_ev("a", 0.1), _ev("b", 0.2)]
        summary = await EvidenceProcessor().synthesize_evidence(_claim(), evidence)
        assert summary == "No highly relevant evidence found"

    async def test_support_wording(self):
        evidence = [
            _ev("yea", 0.9, supports=True),
            _ev("nay", 0.8, supports=False),
            _ev("meh", 0.7, supports=None),
        ]
        summary = await EvidenceProcessor().synthesize_evidence(_claim(), evidence)
        assert "supports" in summary
        assert "refutes" in summary
        assert "is neutral on" in summary


class TestAnalyzeEvidence:
    async def test_empty_list_short_circuits_without_llm(self):
        processor = EvidenceProcessor()
        # If the LLM were invoked, this would raise.
        processor._llm = RunnableLambda(lambda _: (_ for _ in ()).throw(RuntimeError("no call")))
        filtered, summary = await processor.analyze_evidence(_claim(), [])
        assert filtered == []
        assert summary == "No evidence provided"

    async def test_scores_clamped_into_unit_interval(self):
        processor = EvidenceProcessor()
        processor._llm = RunnableLambda(
            lambda _: EvidenceAnalysisOutput(
                evidence_analysis=[
                    EvidenceAnalysisItem(
                        index=0, relevance=1.5, supports=True, credibility=-0.2, reasoning="r"
                    )
                ],
                summary="done",
            )
        )
        evidence = [_ev("s", 0.5)]
        filtered, summary = await processor.analyze_evidence(_claim(), evidence)
        assert filtered[0].relevance_score == 1.0
        assert filtered[0].credibility_score == 0.0
        assert summary == "done"

    async def test_sorted_by_relevance_descending(self):
        processor = EvidenceProcessor()
        processor._llm = RunnableLambda(
            lambda _: EvidenceAnalysisOutput(
                evidence_analysis=[
                    EvidenceAnalysisItem(
                        index=0, relevance=0.3, supports=True, credibility=0.5, reasoning="r"
                    ),
                    EvidenceAnalysisItem(
                        index=1, relevance=0.9, supports=True, credibility=0.5, reasoning="r"
                    ),
                ],
                summary="done",
            )
        )
        evidence = [_ev("low", 0.3), _ev("high", 0.3)]
        filtered, _ = await processor.analyze_evidence(_claim(), evidence)
        assert filtered[0].source == "high"
