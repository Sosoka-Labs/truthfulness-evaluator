"""Tests for VerificationChain post-processing.

The LLM step is replaced with a ``RunnableLambda`` returning a fixed
``VerificationOutput``, which exercises the real evidence formatting, verdict
normalization, confidence adjustment, and error-fallback code paths with no
network. Pattern mirrors ``tests/test_extraction.py``.
"""

from langchain_core.runnables import RunnableLambda
from truthfulness_evaluator.llm.chains.verification import (
    VerificationChain,
    VerificationOutput,
)
from truthfulness_evaluator.models import Claim, Evidence


def _claim() -> Claim:
    return Claim(id="c1", text="Some claim.", source_document="doc.txt")


def _chain_returning(output: VerificationOutput) -> VerificationChain:
    chain = VerificationChain(model_name="gpt-4o")
    chain._llm = RunnableLambda(lambda _: output)
    return chain


def _output(verdict="SUPPORTS", confidence=0.9, key_evidence="") -> VerificationOutput:
    return VerificationOutput(
        verdict=verdict, confidence=confidence, reasoning="because", key_evidence=key_evidence
    )


class TestEvidenceFormatting:
    async def test_support_indicators_rendered_in_prompt(self):
        captured = {}

        def _capture(prompt_value):
            captured["text"] = prompt_value.to_string()
            return _output()

        chain = VerificationChain(model_name="gpt-4o")
        chain._llm = RunnableLambda(_capture)

        evidence = [
            Evidence(
                source="a", source_type="web", content="x", relevance_score=0.9, supports_claim=True
            ),
            Evidence(
                source="b",
                source_type="web",
                content="y",
                relevance_score=0.8,
                supports_claim=False,
            ),
            Evidence(
                source="c", source_type="web", content="z", relevance_score=0.7, supports_claim=None
            ),
        ]
        await chain.verify(_claim(), evidence)
        assert "[SUPPORTS]" in captured["text"]
        assert "[REFUTES]" in captured["text"]
        assert "[NEUTRAL]" in captured["text"]


class TestVerdictNormalization:
    async def test_lowercase_verdict_is_upcased(self):
        chain = _chain_returning(_output(verdict="supports"))
        result = await chain.verify(_claim(), [_ev()])
        assert result.verdict == "SUPPORTS"

    async def test_invalid_verdict_becomes_nei(self):
        chain = _chain_returning(_output(verdict="MAYBE"))
        result = await chain.verify(_claim(), [_ev()])
        assert result.verdict == "NOT_ENOUGH_INFO"

    async def test_model_votes_recorded(self):
        chain = _chain_returning(_output(verdict="REFUTES"))
        result = await chain.verify(_claim(), [_ev()])
        assert result.model_votes == {"gpt-4o": "REFUTES"}


class TestConfidenceAdjustment:
    async def test_confidence_clamped_to_one(self):
        chain = _chain_returning(_output(confidence=1.5))
        result = await chain.verify(_claim(), [_ev()])
        assert result.confidence == 1.0

    async def test_no_evidence_penalizes_confidence(self):
        chain = _chain_returning(_output(confidence=0.9))
        result = await chain.verify(_claim(), [])
        assert result.confidence == 0.3

    async def test_key_evidence_appended_to_explanation(self):
        chain = _chain_returning(_output(key_evidence="the smoking gun"))
        result = await chain.verify(_claim(), [_ev()])
        assert "the smoking gun" in result.explanation


class TestErrorFallback:
    async def test_llm_exception_yields_nei(self):
        def _boom(_):
            raise RuntimeError("model exploded")

        chain = VerificationChain(model_name="gpt-4o")
        chain._llm = RunnableLambda(_boom)
        result = await chain.verify(_claim(), [_ev()])
        assert result.verdict == "NOT_ENOUGH_INFO"
        assert result.confidence == 0.0
        assert "model exploded" in result.explanation


def _ev() -> Evidence:
    return Evidence(source="s", source_type="web", content="c", relevance_score=0.8)
