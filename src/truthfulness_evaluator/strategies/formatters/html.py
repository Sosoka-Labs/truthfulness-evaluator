"""HTML report formatter."""

from truthfulness_evaluator.models import TruthfulnessReport
from truthfulness_evaluator.reporting.generator import ReportGenerator


class HtmlFormatter:
    """Formats truthfulness reports as HTML."""

    def format(self, report: TruthfulnessReport) -> str:
        """Format a truthfulness report as HTML."""
        gen = ReportGenerator(report)
        return gen.to_html()

    def file_extension(self) -> str:
        """Return the file extension for HTML format."""
        return ".html"
