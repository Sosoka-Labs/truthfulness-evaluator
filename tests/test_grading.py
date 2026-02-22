"""Tests for truthfulness_evaluator.core.grading module."""

import pytest
from truthfulness_evaluator.core.grading import (
    build_report,
    calculate_grade,
    calculate_statistics,
    generate_summary,
    is_verified,
)
from truthfulness_evaluator.models import Claim, TruthfulnessStatistics, VerificationResult


class TestCalculateGrade:
    """Tests for calculate_grade function."""

    @pytest.mark.parametrize(
        "support_ratio,confidence,expected_grade",
        [
            (1.0, 0.95, "A+"),  # score = 0.95
            (1.0, 0.90, "A+"),  # score = 0.90
            (1.0, 0.88, "A"),  # score = 0.88
            (1.0, 0.85, "A"),  # score = 0.85
            (1.0, 0.82, "A-"),  # score = 0.82
            (1.0, 0.80, "A-"),  # score = 0.80
            (0.9, 0.85, "B+"),  # score = 0.765
            (0.8, 0.9, "B"),  # score = 0.72
            (0.75, 0.9, "C+"),  # score = 0.675
            (0.7, 0.9, "C+"),  # score = 0.63
            (0.6, 0.95, "C"),  # score = 0.57
            (0.5, 1.0, "C-"),  # score = 0.50
            (0.5, 0.85, "D"),  # score = 0.425
            (0.3, 0.9, "F"),  # score = 0.27
        ],
    )
    def test_calculate_grade_ranges(self, support_ratio, confidence, expected_grade):
        """Test grade calculation across different score ranges."""
        num_verified = 10
        num_supports = int(num_verified * support_ratio)

        verifications = []
        for i in range(num_supports):
            verifications.append(
                VerificationResult(
                    claim_id=f"claim-{i}",
                    verdict="SUPPORTS",
                    confidence=confidence,
                    explanation="Supports",
                )
            )
        for i in range(num_supports, num_verified):
            verifications.append(
                VerificationResult(
                    claim_id=f"claim-{i}",
                    verdict="REFUTES",
                    confidence=confidence,
                    explanation="Refutes",
                )
            )

        grade = calculate_grade(verifications)
        assert grade == expected_grade

    def test_calculate_grade_no_verifications(self):
        """Test grade calculation with no verifications returns F."""
        assert calculate_grade([]) == "F"

    def test_calculate_grade_no_verified_claims(self):
        """Test grade calculation when no claims pass verification threshold."""
        verifications = [
            VerificationResult(
                claim_id="c1",
                verdict="SUPPORTS",
                confidence=0.6,
                explanation="Low confidence",
            ),
            VerificationResult(
                claim_id="c2",
                verdict="NOT_ENOUGH_INFO",
                confidence=0.9,
                explanation="Not enough info",
            ),
        ]

        assert calculate_grade(verifications) == "F"

    def test_calculate_grade_custom_threshold(self):
        """Test grade calculation with custom confidence threshold."""
        verifications = [
            VerificationResult(
                claim_id="c1",
                verdict="SUPPORTS",
                confidence=0.65,
                explanation="ok",
            )
        ]

        # With default 0.7, should be F
        assert calculate_grade(verifications) == "F"

        # With 0.6 threshold, should pass (score = 1.0 * 0.65 = 0.65 -> B-)
        assert calculate_grade(verifications, confidence_threshold=0.6) == "B-"


class TestIsVerified:
    """Tests for is_verified function."""

    def test_supports_high_confidence(self):
        result = VerificationResult(
            claim_id="c1", verdict="SUPPORTS", confidence=0.9, explanation="ok"
        )
        assert is_verified(result) is True

    def test_refutes_high_confidence(self):
        result = VerificationResult(
            claim_id="c1", verdict="REFUTES", confidence=0.85, explanation="ok"
        )
        assert is_verified(result) is True

    def test_supports_low_confidence(self):
        result = VerificationResult(
            claim_id="c1", verdict="SUPPORTS", confidence=0.6, explanation="ok"
        )
        assert is_verified(result) is False

    def test_not_enough_info_never_verified(self):
        result = VerificationResult(
            claim_id="c1", verdict="NOT_ENOUGH_INFO", confidence=0.95, explanation="ok"
        )
        assert is_verified(result) is False

    def test_unverifiable_never_verified(self):
        result = VerificationResult(
            claim_id="c1", verdict="UNVERIFIABLE", confidence=0.95, explanation="ok"
        )
        assert is_verified(result) is False

    def test_boundary_at_default_threshold(self):
        result = VerificationResult(
            claim_id="c1", verdict="SUPPORTS", confidence=0.7, explanation="ok"
        )
        assert is_verified(result) is True

    def test_custom_threshold(self):
        result = VerificationResult(
            claim_id="c1", verdict="SUPPORTS", confidence=0.5, explanation="ok"
        )
        assert is_verified(result) is False
        assert is_verified(result, confidence_threshold=0.5) is True


class TestCalculateStatistics:
    """Tests for calculate_statistics function."""

    def test_calculate_statistics_basic(self):
        """Test statistics calculation with various verdicts."""
        claims = [
            Claim(id=f"c{i}", text=f"Claim {i}", source_document="test.txt") for i in range(5)
        ]
        verifications = [
            VerificationResult(claim_id="c0", verdict="SUPPORTS", confidence=0.9, explanation="ok"),
            VerificationResult(claim_id="c1", verdict="SUPPORTS", confidence=0.8, explanation="ok"),
            VerificationResult(claim_id="c2", verdict="REFUTES", confidence=0.85, explanation="ok"),
            VerificationResult(
                claim_id="c3", verdict="NOT_ENOUGH_INFO", confidence=0.5, explanation="ok"
            ),
            VerificationResult(
                claim_id="c4", verdict="UNVERIFIABLE", confidence=0.4, explanation="ok"
            ),
        ]

        stats = calculate_statistics(claims, verifications)

        assert stats.total_claims == 5
        assert stats.supported == 2
        assert stats.refuted == 1
        assert stats.not_enough_info == 1
        assert stats.unverifiable == 1
        assert stats.verification_rate == pytest.approx(0.6)
        assert stats.accuracy_score == pytest.approx(2 / 3)

    def test_calculate_statistics_empty(self):
        """Test statistics calculation with no data."""
        stats = calculate_statistics([], [])

        assert stats.total_claims == 0
        assert stats.supported == 0
        assert stats.refuted == 0
        assert stats.not_enough_info == 0
        assert stats.unverifiable == 0
        assert stats.verification_rate == 0.0
        assert stats.accuracy_score == 0.0

    def test_calculate_statistics_all_supported(self):
        """Test verification_rate and accuracy_score when all supported."""
        claims = [
            Claim(id=f"c{i}", text=f"Claim {i}", source_document="test.txt") for i in range(3)
        ]
        verifications = [
            VerificationResult(
                claim_id=f"c{i}", verdict="SUPPORTS", confidence=0.9, explanation="ok"
            )
            for i in range(3)
        ]

        stats = calculate_statistics(claims, verifications)
        assert stats.verification_rate == 1.0
        assert stats.accuracy_score == 1.0

    def test_calculate_statistics_all_refuted(self):
        """Test accuracy_score when all refuted."""
        claims = [
            Claim(id=f"c{i}", text=f"Claim {i}", source_document="test.txt") for i in range(3)
        ]
        verifications = [
            VerificationResult(
                claim_id=f"c{i}", verdict="REFUTES", confidence=0.9, explanation="ok"
            )
            for i in range(3)
        ]

        stats = calculate_statistics(claims, verifications)
        assert stats.verification_rate == 1.0
        assert stats.accuracy_score == 0.0


class TestGenerateSummary:
    """Tests for generate_summary function."""

    def test_generate_summary_no_claims(self):
        """Test summary generation with no claims."""
        stats = TruthfulnessStatistics(total_claims=0)
        summary = generate_summary("F", stats)

        assert summary == "No claims were extracted from the document."

    def test_generate_summary_basic_structure(self):
        """Test summary includes basic information."""
        stats = TruthfulnessStatistics(
            total_claims=1,
            supported=1,
            refuted=0,
            not_enough_info=0,
            unverifiable=0,
        )
        summary = generate_summary("A+", stats)

        assert "grade A+" in summary
        assert "1 claims" in summary
        assert "1 were supported" in summary

    def test_generate_summary_low_verification_rate(self):
        """Test summary mentions low verification rate."""
        stats = TruthfulnessStatistics(
            total_claims=10,
            supported=1,
            refuted=0,
            not_enough_info=9,
            unverifiable=0,
            verification_rate=0.1,  # 1/10
            accuracy_score=1.0,
        )
        summary = generate_summary("F", stats)

        assert "Many claims lacked sufficient evidence" in summary

    def test_generate_summary_low_accuracy_score(self):
        """Test summary mentions low accuracy."""
        stats = TruthfulnessStatistics(
            total_claims=6,
            supported=1,
            refuted=3,
            not_enough_info=2,
            unverifiable=0,
            verification_rate=4 / 6,  # 0.67 >= 0.5
            accuracy_score=1 / 4,  # 0.25 < 0.7
        )
        summary = generate_summary("D", stats)

        assert "Several claims were found to be inaccurate" in summary

    def test_generate_summary_high_accuracy(self):
        """Test summary mentions high accuracy."""
        stats = TruthfulnessStatistics(
            total_claims=10,
            supported=8,
            refuted=0,
            not_enough_info=2,
            unverifiable=0,
            verification_rate=0.8,  # 8/10
            accuracy_score=1.0,  # 8/8
        )
        summary = generate_summary("A", stats)

        assert "appears to be largely accurate" in summary


class TestBuildReport:
    """Tests for build_report function."""

    def test_build_report_basic(self):
        """Test building a basic report."""
        claims = [Claim(id="c1", text="Claim", source_document="test.txt")]
        verifications = [
            VerificationResult(claim_id="c1", verdict="SUPPORTS", confidence=0.9, explanation="ok")
        ]

        report = build_report(
            source_document="test.txt",
            claims=claims,
            verifications=verifications,
        )

        assert report.source_document == "test.txt"
        assert len(report.claims) == 1
        assert len(report.verifications) == 1
        assert report.overall_grade == "A+"
        assert report.overall_confidence == pytest.approx(0.9, rel=1e-9)
        assert "grade A+" in report.summary
        assert report.statistics.total_claims == 1
        assert report.statistics.supported == 1

    def test_build_report_with_unvalidated_claims(self):
        """Test that build_report identifies unvalidated claims."""
        claims = [
            Claim(id="c1", text="Claim 1", source_document="test.txt"),
            Claim(id="c2", text="Claim 2", source_document="test.txt"),
        ]
        verifications = [
            VerificationResult(claim_id="c1", verdict="SUPPORTS", confidence=0.9, explanation="ok")
        ]

        report = build_report(
            source_document="test.txt",
            claims=claims,
            verifications=verifications,
        )

        assert len(report.unvalidated_claims) == 1
        assert report.unvalidated_claims[0].id == "c2"

    def test_build_report_override_grade(self):
        """Test that provided grade is not overwritten."""
        verifications = [
            VerificationResult(claim_id="c1", verdict="SUPPORTS", confidence=0.95, explanation="ok")
        ]

        report = build_report(
            source_document="test.txt",
            claims=[],
            verifications=verifications,
            grade="B+",
        )

        assert report.overall_grade == "B+"

    def test_build_report_override_summary(self):
        """Test that provided summary is not overwritten."""
        verifications = [
            VerificationResult(claim_id="c1", verdict="SUPPORTS", confidence=0.9, explanation="ok")
        ]

        custom_summary = "Custom summary text"
        report = build_report(
            source_document="test.txt",
            claims=[],
            verifications=verifications,
            summary=custom_summary,
        )

        assert report.summary == custom_summary

    def test_build_report_no_verifications(self):
        """Test building report with no verifications."""
        report = build_report(
            source_document="test.txt",
            claims=[],
            verifications=[],
        )

        assert report.overall_grade == "F"
        assert report.overall_confidence == 0.0
        assert "No claims were extracted" in report.summary

    def test_build_report_custom_threshold(self):
        """Test building report with custom confidence threshold."""
        verifications = [
            VerificationResult(claim_id="c1", verdict="SUPPORTS", confidence=0.65, explanation="ok")
        ]

        # With default 0.7, should be F
        report1 = build_report(
            source_document="test.txt",
            claims=[],
            verifications=verifications,
        )
        assert report1.overall_grade == "F"

        # With 0.6 threshold, should pass (score = 1.0 * 0.65 = 0.65 -> B-)
        report2 = build_report(
            source_document="test.txt",
            claims=[],
            verifications=verifications,
            confidence_threshold=0.6,
        )
        assert report2.overall_grade == "B-"
