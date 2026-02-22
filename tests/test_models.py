"""Tests for truthfulness_evaluator.models module."""

import pytest
from pydantic import ValidationError

from truthfulness_evaluator.models import (
    Claim,
    Evidence,
    VerificationResult,
    TruthfulnessStatistics,
    TruthfulnessReport,
)
from truthfulness_evaluator.core.grading import is_verified


class TestClaim:
    """Tests for Claim model."""

    def test_claim_creation_with_all_fields(self):
        """Test creating a claim with all fields specified."""
        claim = Claim(
            id="test-001",
            text="Test claim text",
            source_document="document.txt",
            source_span=(0, 15),
            context="Some context around the claim",
            claim_type="explicit",
        )

        assert claim.id == "test-001"
        assert claim.text == "Test claim text"
        assert claim.source_document == "document.txt"
        assert claim.source_span == (0, 15)
        assert claim.context == "Some context around the claim"
        assert claim.claim_type == "explicit"

    def test_claim_creation_with_defaults(self):
        """Test creating a claim with only required fields."""
        claim = Claim(
            id="test-002",
            text="Another claim",
            source_document="doc2.txt",
        )

        assert claim.id == "test-002"
        assert claim.source_span is None
        assert claim.context is None
        assert claim.claim_type == "explicit"

    def test_claim_creation_implicit_type(self):
        """Test creating a claim with implicit type."""
        claim = Claim(
            id="test-003",
            text="Implicit claim",
            source_document="doc.txt",
            claim_type="implicit",
        )

        assert claim.claim_type == "implicit"

    def test_claim_creation_inferred_type(self):
        """Test creating a claim with inferred type."""
        claim = Claim(
            id="test-004",
            text="Inferred claim",
            source_document="doc.txt",
            claim_type="inferred",
        )

        assert claim.claim_type == "inferred"

    def test_claim_str_representation(self):
        """Test string representation of claim."""
        claim = Claim(
            id="test-005",
            text="This is a very long claim text that should be truncated in the string representation to avoid overly long output when debugging",
            source_document="doc.txt",
        )

        str_repr = str(claim)
        assert str_repr.startswith("Claim(test-005):")
        assert "..." in str_repr
        assert len(str_repr.split(":")[1].strip()) <= 83  # 80 chars + ...


class TestEvidence:
    """Tests for Evidence model."""

    def test_evidence_creation_with_all_fields(self):
        """Test creating evidence with all fields."""
        evidence = Evidence(
            source="https://example.com",
            source_type="web",
            content="Supporting evidence content",
            relevance_score=0.95,
            supports_claim=True,
            credibility_score=0.88,
        )

        assert evidence.source == "https://example.com"
        assert evidence.source_type == "web"
        assert evidence.content == "Supporting evidence content"
        assert evidence.relevance_score == 0.95
        assert evidence.supports_claim is True
        assert evidence.credibility_score == 0.88

    def test_evidence_creation_with_defaults(self):
        """Test creating evidence with default credibility score."""
        evidence = Evidence(
            source="/path/to/file.txt",
            source_type="filesystem",
            content="File content",
            relevance_score=0.7,
        )

        assert evidence.supports_claim is None
        assert evidence.credibility_score == 0.5

    def test_evidence_filesystem_source_type(self):
        """Test evidence with filesystem source type."""
        evidence = Evidence(
            source="/data/facts.txt",
            source_type="filesystem",
            content="Local file evidence",
            relevance_score=0.8,
        )

        assert evidence.source_type == "filesystem"

    def test_evidence_knowledge_base_source_type(self):
        """Test evidence with knowledge_base source type."""
        evidence = Evidence(
            source="kb://documents/123",
            source_type="knowledge_base",
            content="KB evidence",
            relevance_score=0.9,
        )

        assert evidence.source_type == "knowledge_base"

    def test_evidence_relevance_score_validation_too_high(self):
        """Test that relevance score must be <= 1.0."""
        with pytest.raises(ValidationError) as exc_info:
            Evidence(
                source="test.txt",
                source_type="filesystem",
                content="content",
                relevance_score=1.5,
            )

        assert "relevance_score" in str(exc_info.value).lower()

    def test_evidence_relevance_score_validation_too_low(self):
        """Test that relevance score must be >= 0.0."""
        with pytest.raises(ValidationError) as exc_info:
            Evidence(
                source="test.txt",
                source_type="filesystem",
                content="content",
                relevance_score=-0.1,
            )

        assert "relevance_score" in str(exc_info.value).lower()

    def test_evidence_credibility_score_validation_too_high(self):
        """Test that credibility score must be <= 1.0."""
        with pytest.raises(ValidationError) as exc_info:
            Evidence(
                source="test.txt",
                source_type="filesystem",
                content="content",
                relevance_score=0.8,
                credibility_score=1.1,
            )

        assert "credibility_score" in str(exc_info.value).lower()

    def test_evidence_credibility_score_validation_too_low(self):
        """Test that credibility score must be >= 0.0."""
        with pytest.raises(ValidationError) as exc_info:
            Evidence(
                source="test.txt",
                source_type="filesystem",
                content="content",
                relevance_score=0.8,
                credibility_score=-0.2,
            )

        assert "credibility_score" in str(exc_info.value).lower()

    def test_evidence_relevance_score_boundary_values(self):
        """Test relevance score at boundary values."""
        # Minimum
        ev_min = Evidence(
            source="test.txt",
            source_type="filesystem",
            content="content",
            relevance_score=0.0,
        )
        assert ev_min.relevance_score == 0.0

        # Maximum
        ev_max = Evidence(
            source="test.txt",
            source_type="filesystem",
            content="content",
            relevance_score=1.0,
        )
        assert ev_max.relevance_score == 1.0


class TestVerificationResult:
    """Tests for VerificationResult model."""

    def test_verification_result_supports_high_confidence(self):
        """Test verification result with SUPPORTS and high confidence."""
        result = VerificationResult(
            claim_id="claim-001",
            verdict="SUPPORTS",
            confidence=0.9,
            explanation="Strong supporting evidence found",
        )

        assert result.verdict == "SUPPORTS"
        assert result.confidence == 0.9
        assert is_verified(result) is True

    def test_verification_result_refutes_high_confidence(self):
        """Test verification result with REFUTES and high confidence."""
        result = VerificationResult(
            claim_id="claim-002",
            verdict="REFUTES",
            confidence=0.85,
            explanation="Evidence contradicts the claim",
        )

        assert result.verdict == "REFUTES"
        assert is_verified(result) is True

    def test_verification_result_supports_low_confidence(self):
        """Test that SUPPORTS with low confidence is not verified."""
        result = VerificationResult(
            claim_id="claim-003",
            verdict="SUPPORTS",
            confidence=0.6,
            explanation="Weak supporting evidence",
        )

        assert is_verified(result) is False

    def test_verification_result_refutes_low_confidence(self):
        """Test that REFUTES with low confidence is not verified."""
        result = VerificationResult(
            claim_id="claim-004",
            verdict="REFUTES",
            confidence=0.65,
            explanation="Some contradicting evidence",
        )

        assert is_verified(result) is False

    def test_verification_result_not_enough_info(self):
        """Test that NOT_ENOUGH_INFO is never verified."""
        result = VerificationResult(
            claim_id="claim-005",
            verdict="NOT_ENOUGH_INFO",
            confidence=0.9,
            explanation="Insufficient evidence",
        )

        assert is_verified(result) is False

    def test_verification_result_unverifiable(self):
        """Test that UNVERIFIABLE is never verified."""
        result = VerificationResult(
            claim_id="claim-006",
            verdict="UNVERIFIABLE",
            confidence=0.95,
            explanation="Claim cannot be verified",
        )

        assert is_verified(result) is False

    def test_verification_result_confidence_threshold_boundary(self):
        """Test is_verified at exactly 0.7 confidence threshold."""
        result = VerificationResult(
            claim_id="claim-007",
            verdict="SUPPORTS",
            confidence=0.7,
            explanation="At threshold",
        )

        assert is_verified(result) is True

    def test_verification_result_with_evidence(self, sample_evidence):
        """Test verification result with evidence list."""
        result = VerificationResult(
            claim_id="claim-008",
            verdict="SUPPORTS",
            confidence=0.85,
            evidence=[sample_evidence],
            explanation="Evidence provided",
        )

        assert len(result.evidence) == 1
        assert result.evidence[0] == sample_evidence

    def test_verification_result_with_model_votes(self):
        """Test verification result with model votes."""
        result = VerificationResult(
            claim_id="claim-009",
            verdict="SUPPORTS",
            confidence=0.8,
            explanation="Consensus reached",
            model_votes={
                "gpt-4o": "SUPPORTS",
                "claude-sonnet-4-5": "SUPPORTS",
                "gpt-4o-mini": "NOT_ENOUGH_INFO",
            },
        )

        assert len(result.model_votes) == 3
        assert result.model_votes["gpt-4o"] == "SUPPORTS"
        assert result.model_votes["gpt-4o-mini"] == "NOT_ENOUGH_INFO"

    def test_verification_result_empty_defaults(self):
        """Test verification result with default empty lists."""
        result = VerificationResult(
            claim_id="claim-010",
            verdict="SUPPORTS",
            confidence=0.75,
            explanation="Default values",
        )

        assert result.evidence == []
        assert result.model_votes == {}


class TestTruthfulnessStatistics:
    """Tests for TruthfulnessStatistics model."""

    def test_statistics_creation_with_all_fields(self):
        """Test creating statistics with all fields."""
        stats = TruthfulnessStatistics(
            total_claims=100,
            supported=60,
            refuted=20,
            not_enough_info=15,
            unverifiable=5,
        )

        assert stats.total_claims == 100
        assert stats.supported == 60
        assert stats.refuted == 20
        assert stats.not_enough_info == 15
        assert stats.unverifiable == 5

    def test_statistics_default_values(self):
        """Test statistics default to zero."""
        stats = TruthfulnessStatistics()

        assert stats.total_claims == 0
        assert stats.supported == 0
        assert stats.refuted == 0
        assert stats.not_enough_info == 0
        assert stats.unverifiable == 0

    def test_statistics_stores_verification_rate(self):
        """Test that verification_rate is stored as a regular field."""
        stats = TruthfulnessStatistics(
            total_claims=100,
            supported=60,
            refuted=20,
            verification_rate=0.8,
            accuracy_score=0.75,
        )

        assert stats.verification_rate == 0.8
        assert stats.accuracy_score == 0.75

    def test_statistics_defaults_to_zero_rates(self):
        """Test that rates default to 0.0."""
        stats = TruthfulnessStatistics(total_claims=0)

        assert stats.verification_rate == 0.0
        assert stats.accuracy_score == 0.0


class TestTruthfulnessReport:
    """Tests for TruthfulnessReport model."""

    def test_report_creation_minimal(self):
        """Test creating a minimal report."""
        report = TruthfulnessReport(source_document="test.txt")

        assert report.source_document == "test.txt"
        assert report.overall_grade is None
        assert report.overall_confidence == 0.0
        assert report.claims == []
        assert report.verifications == []

    def test_report_creation_with_claims_and_verifications(
        self, sample_claim, sample_verification_result_supports
    ):
        """Test creating a report with claims and verifications."""
        from truthfulness_evaluator.core.grading import build_report

        report = build_report(
            source_document="test.txt",
            claims=[sample_claim],
            verifications=[sample_verification_result_supports],
        )

        assert len(report.claims) == 1
        assert len(report.verifications) == 1
        assert report.statistics.total_claims == 1
        assert report.statistics.supported == 1

    def test_report_with_unvalidated_claims(self):
        """Test report with unvalidated claims list."""
        unvalidated = [
            Claim(id="u1", text="Unvalidated claim 1", source_document="test.txt"),
            Claim(id="u2", text="Unvalidated claim 2", source_document="test.txt"),
        ]

        report = TruthfulnessReport(
            source_document="test.txt",
            unvalidated_claims=unvalidated,
        )

        assert len(report.unvalidated_claims) == 2
        assert report.unvalidated_claims[0].id == "u1"

    def test_report_grade_pattern_validation(self):
        """Test that overall_grade must match valid pattern."""
        # Valid grades
        valid_grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]
        for grade in valid_grades:
            report = TruthfulnessReport(
                source_document="test.txt",
                overall_grade=grade,
            )
            assert report.overall_grade == grade

        # Invalid grade
        with pytest.raises(ValidationError) as exc_info:
            TruthfulnessReport(
                source_document="test.txt",
                overall_grade="X",
            )
        assert "overall_grade" in str(exc_info.value).lower()
