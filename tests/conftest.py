"""Shared pytest fixtures for truthfulness-evaluator tests."""

import pytest
from pathlib import Path

from truthfulness_evaluator.models import (
    Claim,
    Evidence,
    VerificationResult,
    TruthfulnessReport,
    TruthfulnessStatistics,
)
from truthfulness_evaluator.config import EvaluatorConfig


@pytest.fixture
def sample_claim() -> Claim:
    """Create a sample claim for testing."""
    return Claim(
        id="claim-001",
        text="Python 3.11 introduced improved error messages and performance optimizations.",
        source_document="/path/to/document.txt",
        source_span=(100, 180),
        context="Python 3.11 was released in October 2022.",
        claim_type="explicit",
    )


@pytest.fixture
def sample_claim_minimal() -> Claim:
    """Create a minimal claim with only required fields."""
    return Claim(
        id="claim-002",
        text="Water boils at 100 degrees Celsius at sea level.",
        source_document="test.txt",
    )


@pytest.fixture
def sample_evidence() -> Evidence:
    """Create sample evidence for testing."""
    return Evidence(
        source="https://docs.python.org/3/whatsnew/3.11.html",
        source_type="web",
        content="Python 3.11 is between 10-60% faster than Python 3.10",
        relevance_score=0.95,
        supports_claim=True,
        credibility_score=0.98,
    )


@pytest.fixture
def sample_evidence_minimal() -> Evidence:
    """Create minimal evidence with defaults."""
    return Evidence(
        source="/data/facts.txt",
        source_type="filesystem",
        content="Water boiling point is 100C at standard atmospheric pressure",
        relevance_score=0.85,
    )


@pytest.fixture
def sample_verification_result_supports(sample_evidence: Evidence) -> VerificationResult:
    """Create a verification result with SUPPORTS verdict."""
    return VerificationResult(
        claim_id="claim-001",
        verdict="SUPPORTS",
        confidence=0.9,
        evidence=[sample_evidence],
        explanation="Multiple credible sources confirm this claim.",
        model_votes={
            "gpt-4o": "SUPPORTS",
            "claude-sonnet-4-5": "SUPPORTS",
        },
    )


@pytest.fixture
def sample_verification_result_refutes() -> VerificationResult:
    """Create a verification result with REFUTES verdict."""
    return VerificationResult(
        claim_id="claim-002",
        verdict="REFUTES",
        confidence=0.85,
        evidence=[],
        explanation="Evidence contradicts this claim.",
        model_votes={
            "gpt-4o": "REFUTES",
            "claude-sonnet-4-5": "REFUTES",
        },
    )


@pytest.fixture
def sample_verification_result_not_enough_info() -> VerificationResult:
    """Create a verification result with NOT_ENOUGH_INFO verdict."""
    return VerificationResult(
        claim_id="claim-003",
        verdict="NOT_ENOUGH_INFO",
        confidence=0.5,
        evidence=[],
        explanation="Insufficient evidence to verify this claim.",
    )


@pytest.fixture
def sample_verification_result_low_confidence() -> VerificationResult:
    """Create a verification result with low confidence."""
    return VerificationResult(
        claim_id="claim-004",
        verdict="SUPPORTS",
        confidence=0.6,
        evidence=[],
        explanation="Some supporting evidence found but confidence is low.",
    )


@pytest.fixture
def sample_statistics() -> TruthfulnessStatistics:
    """Create sample statistics."""
    return TruthfulnessStatistics(
        total_claims=10,
        supported=6,
        refuted=2,
        not_enough_info=1,
        unverifiable=1,
    )


@pytest.fixture
def sample_truthfulness_report(
    sample_claim: Claim,
    sample_verification_result_supports: VerificationResult,
) -> TruthfulnessReport:
    """Create a complete truthfulness report."""
    return TruthfulnessReport(
        source_document="/path/to/document.txt",
        claims=[sample_claim],
        verifications=[sample_verification_result_supports],
    )


@pytest.fixture
def empty_truthfulness_report() -> TruthfulnessReport:
    """Create an empty truthfulness report."""
    return TruthfulnessReport(
        source_document="empty.txt",
        claims=[],
        verifications=[],
    )


@pytest.fixture
def test_config() -> EvaluatorConfig:
    """Create a test configuration with defaults."""
    return EvaluatorConfig(
        openai_api_key="test-openai-key",
        anthropic_api_key="test-anthropic-key",
    )


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for tests."""
    return tmp_path
