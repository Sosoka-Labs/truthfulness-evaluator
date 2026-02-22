"""Tests for truthfulness_evaluator.reporting module."""

import json
from pathlib import Path

import pytest

from truthfulness_evaluator.models import (
    Claim,
    Evidence,
    VerificationResult,
    TruthfulnessReport,
)
from truthfulness_evaluator.reporting import ReportGenerator, generate_report


class TestReportGeneratorJSON:
    """Tests for ReportGenerator.to_json()."""

    def test_to_json_returns_valid_json(self, sample_truthfulness_report):
        """Test that to_json produces valid JSON."""
        generator = ReportGenerator(sample_truthfulness_report)
        json_output = generator.to_json()

        # Should be parseable as JSON
        parsed = json.loads(json_output)
        assert isinstance(parsed, dict)

    def test_to_json_contains_expected_fields(self, sample_truthfulness_report):
        """Test that JSON output contains expected fields."""
        generator = ReportGenerator(sample_truthfulness_report)
        json_output = generator.to_json()
        parsed = json.loads(json_output)

        assert "source_document" in parsed
        assert "overall_grade" in parsed
        assert "overall_confidence" in parsed
        assert "summary" in parsed
        assert "claims" in parsed
        assert "verifications" in parsed
        assert "statistics" in parsed

    def test_to_json_includes_statistics_fields(self, sample_truthfulness_report):
        """Test that statistics are included in JSON."""
        generator = ReportGenerator(sample_truthfulness_report)
        json_output = generator.to_json()
        parsed = json.loads(json_output)

        stats = parsed["statistics"]
        assert "total_claims" in stats
        assert "supported" in stats
        assert "refuted" in stats
        assert "not_enough_info" in stats
        assert "unverifiable" in stats
        assert "verification_rate" in stats
        assert "accuracy_score" in stats

    def test_to_json_custom_indent(self, sample_truthfulness_report):
        """Test that custom indent parameter works."""
        generator = ReportGenerator(sample_truthfulness_report)

        # Default indent=2
        json_default = generator.to_json()
        # Custom indent=4
        json_custom = generator.to_json(indent=4)

        # Both should be valid JSON
        parsed_default = json.loads(json_default)
        parsed_custom = json.loads(json_custom)

        # Content should be identical
        assert parsed_default == parsed_custom

        # Custom indent should produce longer output due to more whitespace
        assert len(json_custom) > len(json_default)

    def test_to_json_empty_report(self, empty_truthfulness_report):
        """Test JSON generation for empty report."""
        generator = ReportGenerator(empty_truthfulness_report)
        json_output = generator.to_json()
        parsed = json.loads(json_output)

        assert parsed["claims"] == []
        assert parsed["verifications"] == []
        assert parsed["statistics"]["total_claims"] == 0

    def test_to_json_includes_evidence(self):
        """Test that evidence is included in JSON output."""
        from truthfulness_evaluator.core.grading import build_report

        evidence = Evidence(
            source="https://example.com",
            source_type="web",
            content="Test evidence content",
            relevance_score=0.9,
            supports_claim=True,
        )
        verification = VerificationResult(
            claim_id="c1",
            verdict="SUPPORTS",
            confidence=0.85,
            evidence=[evidence],
            explanation="Test explanation",
        )
        report = build_report(
            source_document="test.txt",
            claims=[],
            verifications=[verification],
        )

        generator = ReportGenerator(report)
        json_output = generator.to_json()
        parsed = json.loads(json_output)

        assert len(parsed["verifications"][0]["evidence"]) == 1
        assert parsed["verifications"][0]["evidence"][0]["source"] == "https://example.com"


class TestReportGeneratorMarkdown:
    """Tests for ReportGenerator.to_markdown()."""

    def test_to_markdown_contains_header(self, sample_truthfulness_report):
        """Test that markdown output contains header."""
        generator = ReportGenerator(sample_truthfulness_report)
        md_output = generator.to_markdown()

        assert "# Truthfulness Evaluation Report" in md_output

    def test_to_markdown_contains_document_name(self, sample_truthfulness_report):
        """Test that markdown includes document name."""
        generator = ReportGenerator(sample_truthfulness_report)
        md_output = generator.to_markdown()

        assert "**Document:**" in md_output
        assert sample_truthfulness_report.source_document in md_output

    def test_to_markdown_contains_grade(self, sample_truthfulness_report):
        """Test that markdown includes grade."""
        generator = ReportGenerator(sample_truthfulness_report)
        md_output = generator.to_markdown()

        assert "**Grade**" in md_output
        assert sample_truthfulness_report.overall_grade in md_output

    def test_to_markdown_contains_statistics(self, sample_truthfulness_report):
        """Test that markdown includes statistics table."""
        generator = ReportGenerator(sample_truthfulness_report)
        md_output = generator.to_markdown()

        assert "## Summary" in md_output
        assert "**Confidence**" in md_output
        assert "**Total Claims**" in md_output
        assert "**Supported**" in md_output
        assert "**Refuted**" in md_output
        assert "**Not Enough Info**" in md_output

    def test_to_markdown_contains_detailed_results_section(self, sample_truthfulness_report):
        """Test that markdown includes detailed results section."""
        generator = ReportGenerator(sample_truthfulness_report)
        md_output = generator.to_markdown()

        assert "## Detailed Results" in md_output

    def test_to_markdown_includes_verdict_emojis(self):
        """Test that markdown includes emoji for verdicts."""
        from truthfulness_evaluator.core.grading import build_report

        claims = [
            Claim(id="c1", text="Claim 1", source_document="test.txt"),
            Claim(id="c2", text="Claim 2", source_document="test.txt"),
            Claim(id="c3", text="Claim 3", source_document="test.txt"),
        ]
        verifications = [
            VerificationResult(
                claim_id="c1", verdict="SUPPORTS", confidence=0.9, explanation="ok"
            ),
            VerificationResult(
                claim_id="c2", verdict="REFUTES", confidence=0.85, explanation="ok"
            ),
            VerificationResult(
                claim_id="c3", verdict="NOT_ENOUGH_INFO", confidence=0.5, explanation="ok"
            ),
        ]
        report = build_report(
            source_document="test.txt",
            claims=claims,
            verifications=verifications,
        )

        generator = ReportGenerator(report)
        md_output = generator.to_markdown()

        # Check for emojis
        assert "✅" in md_output  # SUPPORTS
        assert "❌" in md_output  # REFUTES
        assert "⚠️" in md_output  # NOT_ENOUGH_INFO

    def test_to_markdown_includes_model_votes(self):
        """Test that markdown includes model votes when present."""
        from truthfulness_evaluator.core.grading import build_report

        verification = VerificationResult(
            claim_id="c1",
            verdict="SUPPORTS",
            confidence=0.9,
            explanation="ok",
            model_votes={
                "gpt-4o": "SUPPORTS",
                "claude-sonnet-4-5": "SUPPORTS",
            },
        )
        claim = Claim(id="c1", text="Test claim", source_document="test.txt")
        report = build_report(
            source_document="test.txt",
            claims=[claim],
            verifications=[verification],
        )

        generator = ReportGenerator(report)
        md_output = generator.to_markdown()

        assert "**Model Votes:**" in md_output

    def test_to_markdown_includes_evidence(self):
        """Test that markdown includes evidence when present."""
        from truthfulness_evaluator.core.grading import build_report

        evidence = Evidence(
            source="https://example.com/article.html",
            source_type="web",
            content="Supporting evidence",
            relevance_score=0.92,
        )
        verification = VerificationResult(
            claim_id="c1",
            verdict="SUPPORTS",
            confidence=0.9,
            evidence=[evidence],
            explanation="ok",
        )
        claim = Claim(id="c1", text="Test claim", source_document="test.txt")
        report = build_report(
            source_document="test.txt",
            claims=[claim],
            verifications=[verification],
        )

        generator = ReportGenerator(report)
        md_output = generator.to_markdown()

        assert "**Evidence:**" in md_output
        assert "92%" in md_output  # relevance score

    def test_to_markdown_includes_explanation(self):
        """Test that markdown includes explanation."""
        from truthfulness_evaluator.core.grading import build_report

        verification = VerificationResult(
            claim_id="c1",
            verdict="SUPPORTS",
            confidence=0.9,
            explanation="This is a detailed explanation of why the claim is supported.",
        )
        claim = Claim(id="c1", text="Test claim", source_document="test.txt")
        report = build_report(
            source_document="test.txt",
            claims=[claim],
            verifications=[verification],
        )

        generator = ReportGenerator(report)
        md_output = generator.to_markdown()

        assert "**Explanation:**" in md_output
        assert "This is a detailed explanation" in md_output

    def test_to_markdown_truncates_long_explanation(self):
        """Test that very long explanations are truncated."""
        from truthfulness_evaluator.core.grading import build_report

        long_explanation = "x" * 600
        verification = VerificationResult(
            claim_id="c1",
            verdict="SUPPORTS",
            confidence=0.9,
            explanation=long_explanation,
        )
        claim = Claim(id="c1", text="Test claim", source_document="test.txt")
        report = build_report(
            source_document="test.txt",
            claims=[claim],
            verifications=[verification],
        )

        generator = ReportGenerator(report)
        md_output = generator.to_markdown()

        # Should be truncated to 500 chars with ellipsis
        assert "> ..." in md_output

    def test_to_markdown_includes_unvalidated_claims(self):
        """Test that markdown includes unvalidated claims section."""
        unvalidated = [
            Claim(id="u1", text="Unvalidated claim 1", source_document="test.txt"),
            Claim(id="u2", text="Unvalidated claim 2", source_document="test.txt"),
        ]
        report = TruthfulnessReport(
            source_document="test.txt",
            unvalidated_claims=unvalidated,
        )

        generator = ReportGenerator(report)
        md_output = generator.to_markdown()

        assert "## Unvalidated Claims" in md_output
        assert "Unvalidated claim 1" in md_output
        assert "Unvalidated claim 2" in md_output

    def test_to_markdown_empty_report(self, empty_truthfulness_report):
        """Test markdown generation for empty report."""
        generator = ReportGenerator(empty_truthfulness_report)
        md_output = generator.to_markdown()

        assert "# Truthfulness Evaluation Report" in md_output
        assert "0" in md_output  # Zero claims


class TestReportGeneratorHTML:
    """Tests for ReportGenerator.to_html()."""

    def test_to_html_contains_doctype(self, sample_truthfulness_report):
        """Test that HTML output starts with DOCTYPE."""
        generator = ReportGenerator(sample_truthfulness_report)
        html_output = generator.to_html()

        assert html_output.strip().startswith("<!DOCTYPE html>")

    def test_to_html_contains_html_tags(self, sample_truthfulness_report):
        """Test that HTML output contains proper structure."""
        generator = ReportGenerator(sample_truthfulness_report)
        html_output = generator.to_html()

        assert "<html" in html_output
        assert "</html>" in html_output
        assert "<head>" in html_output
        assert "</head>" in html_output
        assert "<body>" in html_output
        assert "</body>" in html_output

    def test_to_html_contains_css_styling(self, sample_truthfulness_report):
        """Test that HTML output contains CSS styles."""
        generator = ReportGenerator(sample_truthfulness_report)
        html_output = generator.to_html()

        assert "<style>" in html_output
        assert "</style>" in html_output
        assert ":root" in html_output
        assert "--color-success" in html_output

    def test_to_html_contains_grade_badge(self, sample_truthfulness_report):
        """Test that HTML includes grade badge."""
        generator = ReportGenerator(sample_truthfulness_report)
        html_output = generator.to_html()

        assert "grade-badge" in html_output
        assert sample_truthfulness_report.overall_grade in html_output

    def test_to_html_contains_statistics(self, sample_truthfulness_report):
        """Test that HTML includes statistics."""
        generator = ReportGenerator(sample_truthfulness_report)
        html_output = generator.to_html()

        assert "stats-grid" in html_output
        assert "Total Claims" in html_output
        assert "Supported" in html_output
        assert "Refuted" in html_output
        assert "Not Enough Info" in html_output

    def test_to_html_includes_claim_cards(self):
        """Test that HTML includes claim cards."""
        from truthfulness_evaluator.core.grading import build_report

        claim = Claim(id="c1", text="Test claim", source_document="test.txt")
        verification = VerificationResult(
            claim_id="c1",
            verdict="SUPPORTS",
            confidence=0.9,
            explanation="Test explanation",
        )
        report = build_report(
            source_document="test.txt",
            claims=[claim],
            verifications=[verification],
        )

        generator = ReportGenerator(report)
        html_output = generator.to_html()

        assert "claim-card" in html_output
        assert "Test claim" in html_output

    def test_to_html_includes_verdict_badges(self):
        """Test that HTML includes verdict badges."""
        from truthfulness_evaluator.core.grading import build_report

        claims = [
            Claim(id="c1", text="Claim 1", source_document="test.txt"),
            Claim(id="c2", text="Claim 2", source_document="test.txt"),
        ]
        verifications = [
            VerificationResult(
                claim_id="c1", verdict="SUPPORTS", confidence=0.9, explanation="ok"
            ),
            VerificationResult(
                claim_id="c2", verdict="REFUTES", confidence=0.85, explanation="ok"
            ),
        ]
        report = build_report(
            source_document="test.txt",
            claims=claims,
            verifications=verifications,
        )

        generator = ReportGenerator(report)
        html_output = generator.to_html()

        assert "SUPPORTED" in html_output
        assert "REFUTED" in html_output
        assert "badge-success" in html_output
        assert "badge-danger" in html_output

    def test_to_html_includes_confidence_percentage(self):
        """Test that HTML shows confidence as percentage."""
        from truthfulness_evaluator.core.grading import build_report

        claim = Claim(id="c1", text="Test claim", source_document="test.txt")
        verification = VerificationResult(
            claim_id="c1",
            verdict="SUPPORTS",
            confidence=0.87,
            explanation="ok",
        )
        report = build_report(
            source_document="test.txt",
            claims=[claim],
            verifications=[verification],
        )

        generator = ReportGenerator(report)
        html_output = generator.to_html()

        assert "87%" in html_output

    def test_to_html_includes_evidence_section(self):
        """Test that HTML includes evidence section when present."""
        from truthfulness_evaluator.core.grading import build_report

        evidence = Evidence(
            source="/path/to/file.txt",
            source_type="filesystem",
            content="Evidence content",
            relevance_score=0.95,
        )
        claim = Claim(id="c1", text="Test claim", source_document="test.txt")
        verification = VerificationResult(
            claim_id="c1",
            verdict="SUPPORTS",
            confidence=0.9,
            evidence=[evidence],
            explanation="ok",
        )
        report = build_report(
            source_document="test.txt",
            claims=[claim],
            verifications=[verification],
        )

        generator = ReportGenerator(report)
        html_output = generator.to_html()

        assert "evidence-list" in html_output
        assert "95%" in html_output

    def test_to_html_includes_explanation(self):
        """Test that HTML includes explanation section."""
        from truthfulness_evaluator.core.grading import build_report

        claim = Claim(id="c1", text="Test claim", source_document="test.txt")
        verification = VerificationResult(
            claim_id="c1",
            verdict="SUPPORTS",
            confidence=0.9,
            explanation="This is the explanation of the verdict.",
        )
        report = build_report(
            source_document="test.txt",
            claims=[claim],
            verifications=[verification],
        )

        generator = ReportGenerator(report)
        html_output = generator.to_html()

        assert "explanation" in html_output
        assert "This is the explanation" in html_output

    def test_to_html_truncates_long_explanation(self):
        """Test that HTML truncates very long explanations."""
        from truthfulness_evaluator.core.grading import build_report

        long_explanation = "x" * 400
        claim = Claim(id="c1", text="Test claim", source_document="test.txt")
        verification = VerificationResult(
            claim_id="c1",
            verdict="SUPPORTS",
            confidence=0.9,
            explanation=long_explanation,
        )
        report = build_report(
            source_document="test.txt",
            claims=[claim],
            verifications=[verification],
        )

        generator = ReportGenerator(report)
        html_output = generator.to_html()

        # Should be truncated to 300 chars
        assert "..." in html_output

    def test_to_html_includes_footer(self, sample_truthfulness_report):
        """Test that HTML includes footer."""
        generator = ReportGenerator(sample_truthfulness_report)
        html_output = generator.to_html()

        assert "<footer" in html_output
        assert "Generated by Truthfulness Evaluator" in html_output

    def test_to_html_empty_report(self, empty_truthfulness_report):
        """Test HTML generation for empty report."""
        generator = ReportGenerator(empty_truthfulness_report)
        html_output = generator.to_html()

        assert "<!DOCTYPE html>" in html_output
        assert "0" in html_output


class TestReportGeneratorSave:
    """Tests for ReportGenerator.save()."""

    def test_save_json_format_auto_detect(self, sample_truthfulness_report, temp_dir):
        """Test saving JSON with auto-detected format."""
        generator = ReportGenerator(sample_truthfulness_report)
        output_path = temp_dir / "report.json"

        generator.save(str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        # Should be valid JSON
        parsed = json.loads(content)
        assert parsed["source_document"] == sample_truthfulness_report.source_document

    def test_save_markdown_format_auto_detect(self, sample_truthfulness_report, temp_dir):
        """Test saving Markdown with auto-detected format."""
        generator = ReportGenerator(sample_truthfulness_report)
        output_path = temp_dir / "report.md"

        generator.save(str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        assert "# Truthfulness Evaluation Report" in content

    def test_save_markdown_format_auto_detect_markdown_extension(
        self, sample_truthfulness_report, temp_dir
    ):
        """Test saving with .markdown extension."""
        generator = ReportGenerator(sample_truthfulness_report)
        output_path = temp_dir / "report.markdown"

        generator.save(str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        assert "# Truthfulness Evaluation Report" in content

    def test_save_html_format_auto_detect(self, sample_truthfulness_report, temp_dir):
        """Test saving HTML with auto-detected format."""
        generator = ReportGenerator(sample_truthfulness_report)
        output_path = temp_dir / "report.html"

        generator.save(str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        assert "<!DOCTYPE html>" in content

    def test_save_explicit_json_format(self, sample_truthfulness_report, temp_dir):
        """Test saving with explicit json format."""
        generator = ReportGenerator(sample_truthfulness_report)
        output_path = temp_dir / "report.txt"

        generator.save(str(output_path), format="json")

        content = output_path.read_text()
        parsed = json.loads(content)
        assert "source_document" in parsed

    def test_save_explicit_markdown_format(self, sample_truthfulness_report, temp_dir):
        """Test saving with explicit markdown format."""
        generator = ReportGenerator(sample_truthfulness_report)
        output_path = temp_dir / "report.txt"

        generator.save(str(output_path), format="markdown")

        content = output_path.read_text()
        assert "# Truthfulness Evaluation Report" in content

    def test_save_explicit_html_format(self, sample_truthfulness_report, temp_dir):
        """Test saving with explicit html format."""
        generator = ReportGenerator(sample_truthfulness_report)
        output_path = temp_dir / "report.txt"

        generator.save(str(output_path), format="html")

        content = output_path.read_text()
        assert "<!DOCTYPE html>" in content

    def test_save_default_format_when_unknown_extension(
        self, sample_truthfulness_report, temp_dir
    ):
        """Test that unknown extensions default to markdown."""
        generator = ReportGenerator(sample_truthfulness_report)
        output_path = temp_dir / "report.xyz"

        generator.save(str(output_path))

        content = output_path.read_text()
        assert "# Truthfulness Evaluation Report" in content

    def test_save_creates_utf8_file(self, sample_truthfulness_report, temp_dir):
        """Test that saved file uses UTF-8 encoding."""
        from truthfulness_evaluator.core.grading import build_report

        # Create a report with unicode characters — need a matching verification
        # so the claim appears in the Detailed Results section
        claim = Claim(id="c1", text="Test émojis: ✅ ❌ 🎉", source_document="test.txt")
        verification = VerificationResult(
            claim_id="c1",
            verdict="SUPPORTS",
            confidence=0.9,
            explanation="ok",
        )
        report = build_report(
            source_document="test.txt",
            claims=[claim],
            verifications=[verification],
        )

        generator = ReportGenerator(report)
        output_path = temp_dir / "report.md"

        generator.save(str(output_path))

        # Should be readable as UTF-8
        content = output_path.read_text(encoding="utf-8")
        assert "émojis" in content
        assert "✅" in content


class TestGenerateReport:
    """Tests for generate_report() convenience function."""

    def test_generate_report_json_format(self, sample_truthfulness_report):
        """Test generate_report with json format."""
        output = generate_report(sample_truthfulness_report, format="json")

        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed["source_document"] == sample_truthfulness_report.source_document

    def test_generate_report_markdown_format(self, sample_truthfulness_report):
        """Test generate_report with markdown format."""
        output = generate_report(sample_truthfulness_report, format="markdown")

        assert "# Truthfulness Evaluation Report" in output

    def test_generate_report_html_format(self, sample_truthfulness_report):
        """Test generate_report with html format."""
        output = generate_report(sample_truthfulness_report, format="html")

        assert "<!DOCTYPE html>" in output

    def test_generate_report_default_format(self, sample_truthfulness_report):
        """Test generate_report defaults to markdown."""
        output = generate_report(sample_truthfulness_report)

        assert "# Truthfulness Evaluation Report" in output

    def test_generate_report_unknown_format_defaults_to_markdown(
        self, sample_truthfulness_report
    ):
        """Test that unknown format defaults to markdown."""
        output = generate_report(sample_truthfulness_report, format="unknown")

        assert "# Truthfulness Evaluation Report" in output

    def test_generate_report_empty_report(self, empty_truthfulness_report):
        """Test generate_report with empty report."""
        output = generate_report(empty_truthfulness_report, format="json")

        parsed = json.loads(output)
        assert parsed["claims"] == []
