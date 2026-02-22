"""JSON report formatter."""

from ..models import TruthfulnessReport


class JsonFormatter:
    """Formats truthfulness reports as JSON."""

    def __init__(self, indent: int = 2):
        self._indent = indent

    def format(self, report: TruthfulnessReport) -> str:
        """Format a truthfulness report as JSON."""
        return report.model_dump_json(indent=self._indent)

    def file_extension(self) -> str:
        """Return the file extension for JSON format."""
        return ".json"
