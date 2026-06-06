"""Markdown report formatter."""

from truthfulness_evaluator.models import TruthfulnessReport
from truthfulness_evaluator.reporting.generator import ReportGenerator


class MarkdownFormatter:
    """Formats truthfulness reports as Markdown."""

    def format(self, report: TruthfulnessReport) -> str:
        """Format a truthfulness report as Markdown."""
        gen = ReportGenerator(report)
        return gen.to_markdown()

    def file_extension(self) -> str:
        """Return the file extension for Markdown format."""
        return ".md"
