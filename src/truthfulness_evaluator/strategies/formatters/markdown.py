"""Markdown report formatter."""

from ...models import TruthfulnessReport


class MarkdownFormatter:
    """Formats truthfulness reports as Markdown."""

    def format(self, report: TruthfulnessReport) -> str:
        """Format a truthfulness report as Markdown."""
        from ...reporting.generator import ReportGenerator

        gen = ReportGenerator(report)
        return gen.to_markdown()

    def file_extension(self) -> str:
        """Return the file extension for Markdown format."""
        return ".md"
