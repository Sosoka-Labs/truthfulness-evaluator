"""End-to-end tests driving the full LangGraph pipelines.

Two tiers:

* **Fake-LLM (default, $0, deterministic):** ``create_chat_model`` is patched in
  the specific chain modules the graph touches, so the external and internal
  graphs run end to end and produce a real ``TruthfulnessReport`` with no
  network. Web/filesystem search is disabled; the internal graph is routed to
  the pure keyword ("behavioral") verifier against a seeded fake repo.
* **Real-AI (``@pytest.mark.e2e``, on demand):** exercises the graph with real
  models over seeded known assets. Deselected by default (CI runs
  ``-m "not e2e"``) and skipped unless ``OPENAI_API_KEY`` is set. The model is
  configurable via ``TRUTH_E2E_MODEL`` (default ``gpt-4o-mini``) so cost stays
  under the caller's control.
"""

import os
from pathlib import Path

import pytest
from langchain_core.runnables import RunnableLambda
from truthfulness_evaluator.llm.chains.extraction import ClaimExtractionOutput, ExtractedClaim
from truthfulness_evaluator.llm.chains.internal_verification import ClaimClassification
from truthfulness_evaluator.llm.chains.verification import VerificationOutput
from truthfulness_evaluator.llm.workflows.graph import create_truthfulness_graph
from truthfulness_evaluator.llm.workflows.graph_internal import create_internal_verification_graph
from truthfulness_evaluator.models import TruthfulnessReport

FIXTURES = Path(__file__).parent / "fixtures"
FAKE_REPO = FIXTURES / "fake_repo"

HAS_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
E2E_MODEL = os.getenv("TRUTH_E2E_MODEL", "gpt-4o-mini")


# =============================================================================
# Fake-LLM support
# =============================================================================


class _FakeStructuredModel:
    """Stands in for a chat model; ``with_structured_output`` yields fixed data."""

    def __init__(self, responses: dict):
        self._responses = responses

    def with_structured_output(self, schema, **kwargs):
        factory = self._responses.get(schema)
        if factory is None:
            raise AssertionError(f"No fake response registered for {schema.__name__}")
        return RunnableLambda(lambda _: factory())


def _patch_factory(monkeypatch, module_path: str, responses: dict) -> None:
    monkeypatch.setattr(
        f"truthfulness_evaluator.llm.chains.{module_path}.create_chat_model",
        lambda *a, **k: _FakeStructuredModel(responses),
    )


# =============================================================================
# Fake-LLM end-to-end (default, deterministic)
# =============================================================================


class TestExternalGraphWithFakeLLM:
    async def test_produces_report(self, monkeypatch):
        responses = {
            ClaimExtractionOutput: lambda: ClaimExtractionOutput(
                claims=[ExtractedClaim(text="The sky appears blue.", claim_type="explicit")]
            ),
            VerificationOutput: lambda: VerificationOutput(
                verdict="SUPPORTS", confidence=0.9, reasoning="fake", key_evidence=""
            ),
        }
        _patch_factory(monkeypatch, "extraction", responses)
        _patch_factory(monkeypatch, "verification", responses)

        state = {
            "document": "The sky appears blue.",
            "document_path": "doc.md",
            "root_path": None,
            "claims": [],
            "current_claim_index": 0,
            "verifications": [],
            "evidence_cache": {},
            "config": {
                "enable_web_search": False,
                "enable_filesystem_search": False,
                "verification_models": ["fake"],
                "claim_extraction_model": "fake",
                # With no evidence gathered, VerificationChain caps confidence at
                # 0.3; keep the consensus threshold below that so the SUPPORTS
                # verdict propagates through the full graph.
                "confidence_threshold": 0.2,
            },
            "final_report": None,
        }

        graph = create_truthfulness_graph()
        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "ext-fake"}})

        report = result["final_report"]
        assert isinstance(report, TruthfulnessReport)
        assert report.statistics.total_claims == 1
        assert result["verifications"][0].verdict == "SUPPORTS"


class TestInternalGraphWithFakeLLM:
    async def test_behavioral_claim_verified_against_fake_repo(self, monkeypatch):
        responses = {
            ClaimExtractionOutput: lambda: ClaimExtractionOutput(
                claims=[
                    ExtractedClaim(text="It uses Pydantic for validation.", claim_type="explicit")
                ]
            ),
            ClaimClassification: lambda: ClaimClassification(
                claim_type="behavioral", confidence=0.9, reasoning="fake"
            ),
        }
        _patch_factory(monkeypatch, "extraction", responses)
        _patch_factory(monkeypatch, "internal_verification", responses)

        state = {
            "document": "It uses Pydantic for validation.",
            "document_path": "docs.md",
            "root_path": str(FAKE_REPO),
            "claims": [],
            "current_claim_index": 0,
            "verifications": [],
            "evidence_cache": {},
            "config": {
                "enable_web_search": False,
                "claim_extraction_model": "fake",
                "verification_models": ["fake"],
            },
            "final_report": None,
            "verification_mode": "internal",
            "classifications": {},
        }

        graph = create_internal_verification_graph()
        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "int-fake"}})

        report = result["final_report"]
        assert isinstance(report, TruthfulnessReport)
        assert report.statistics.total_claims == 1
        verification = result["verifications"][0]
        assert verification.verdict == "SUPPORTS"
        # Behavioral verifier cites the module that contains the keyword.
        assert any("calculator.py" in e.source for e in verification.evidence)


# =============================================================================
# Real-AI end-to-end (gated, on demand)
# =============================================================================


@pytest.mark.e2e
@pytest.mark.skipif(not HAS_OPENAI, reason="requires OPENAI_API_KEY")
class TestRealAI:
    async def test_external_true_claim_not_refuted(self):
        document = (FIXTURES / "e2e_external_doc.md").read_text()
        state = {
            "document": document,
            "document_path": str(FIXTURES / "e2e_external_doc.md"),
            "root_path": None,
            "claims": [],
            "current_claim_index": 0,
            "verifications": [],
            "evidence_cache": {},
            "config": {
                "enable_web_search": True,
                "enable_filesystem_search": False,
                "claim_extraction_model": E2E_MODEL,
                "verification_models": [E2E_MODEL],
                "confidence_threshold": 0.5,
            },
            "final_report": None,
        }
        graph = create_truthfulness_graph()
        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "ext-real"}})

        report = result["final_report"]
        assert isinstance(report, TruthfulnessReport)
        assert report.statistics.total_claims >= 1
        # A document of plain true facts must not come back mostly refuted.
        assert report.statistics.refuted == 0

    async def test_internal_version_claim_supported(self):
        document = "This project requires Python 3.11 or higher."
        state = {
            "document": document,
            "document_path": "docs.md",
            "root_path": str(FAKE_REPO),
            "claims": [],
            "current_claim_index": 0,
            "verifications": [],
            "evidence_cache": {},
            "config": {
                "enable_web_search": False,
                "claim_extraction_model": E2E_MODEL,
                "verification_models": [E2E_MODEL],
                "confidence_threshold": 0.5,
            },
            "final_report": None,
            "verification_mode": "internal",
            "classifications": {},
        }
        graph = create_internal_verification_graph()
        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "int-real"}})

        report = result["final_report"]
        assert isinstance(report, TruthfulnessReport)
        assert report.statistics.total_claims >= 1
        # pyproject.toml pins requires-python = ">=3.11"; the claim is true.
        assert all(v.verdict != "REFUTES" for v in result["verifications"])
