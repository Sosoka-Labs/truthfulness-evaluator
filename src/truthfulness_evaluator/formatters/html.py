"""HTML report formatter."""

from ..models import TruthfulnessReport


class HtmlFormatter:
    """Formats truthfulness reports as HTML."""

    def format(self, report: TruthfulnessReport) -> str:
        """Format a truthfulness report as HTML."""
        from ..reporting.generator import ReportGenerator

        gen = ReportGenerator(report)
        return gen.to_html()

    def file_extension(self) -> str:
        """Return the file extension for HTML format."""
        return ".html"
