# Custom Formatters

Report formatters convert `TruthfulnessReport` objects into output formats like JSON, Markdown, HTML, or domain-specific formats. The `ReportFormatter` protocol defines the interface.

## Protocol Interface

```python
from typing import Protocol
from truthfulness_evaluator.models import TruthfulnessReport

class ReportFormatter(Protocol):
    def format(self, report: TruthfulnessReport) -> str:
        """Format a truthfulness report."""
        ...

    def file_extension(self) -> str:
        """Return the default file extension for this format."""
        ...
```

Unlike other protocols, formatters are **synchronous** (not async) for simplicity.

## Example: CSV Formatter

Here's a custom formatter that outputs verification results as CSV:

```python
import csv
from io import StringIO
from truthfulness_evaluator.models import TruthfulnessReport


class CsvFormatter:
    """Formats truthfulness reports as CSV.

    Useful for importing results into spreadsheets or data analysis tools.
    """

    def __init__(self, include_evidence: bool = False):
        """Initialize CSV formatter.

        Args:
            include_evidence: If True, include evidence sources in output
        """
        self._include_evidence = include_evidence

    def format(self, report: TruthfulnessReport) -> str:
        """Format a truthfulness report as CSV."""
        output = StringIO()

        # Define CSV columns
        fieldnames = [
            "claim_text",
            "verdict",
            "confidence",
            "explanation",
        ]

        if self._include_evidence:
            fieldnames.append("evidence_sources")

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Write verification results
        for result in report.results:
            row = {
                "claim_text": result.claim.text,
                "verdict": result.verdict,
                "confidence": f"{result.confidence:.2f}",
                "explanation": result.explanation.replace("\n", " "),
            }

            if self._include_evidence:
                sources = [e.source for e in result.evidence_used]
                row["evidence_sources"] = "; ".join(sources[:3])

            writer.writerow(row)

        # Add summary statistics as comment
        output.write("\n# Summary Statistics\n")
        output.write(f"# Total Claims,{report.statistics.total_claims}\n")
        output.write(f"# Supported,{report.statistics.supported_claims}\n")
        output.write(f"# Refuted,{report.statistics.refuted_claims}\n")
        output.write(f"# Grade,{report.grade}\n")

        return output.getvalue()

    def file_extension(self) -> str:
        """Return the file extension for CSV format."""
        return ".csv"
```

## Registering with WorkflowConfig

```python
from truthfulness_evaluator.workflows.config import WorkflowConfig
from truthfulness_evaluator.extractors import SimpleExtractor
from truthfulness_evaluator.gatherers import WebSearchGatherer
from truthfulness_evaluator.verifiers import SingleModelVerifier
from truthfulness_evaluator.formatters import JsonFormatter, MarkdownFormatter

config = WorkflowConfig(
    name="multi-format",
    description="Outputs in multiple formats",
    extractor=SimpleExtractor(),
    gatherers=[WebSearchGatherer()],
    verifier=SingleModelVerifier(),
    formatters=[
        JsonFormatter(indent=2),
        MarkdownFormatter(),
        CsvFormatter(include_evidence=True),
    ],
)
```

The workflow will generate all three output files when saving results.

## Built-in Formatters

The library provides three built-in formatters:

- **JsonFormatter**: Machine-readable JSON output with configurable indentation
- **MarkdownFormatter**: Human-readable Markdown with tables and summaries
- **HtmlFormatter**: Rich HTML reports with styling using Jinja2 templates

## Creating Template-Based Formatters

For complex layouts, use Jinja2 templates (like `HtmlFormatter` does):

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

class CustomHtmlFormatter:
    def __init__(self, template_path: Path):
        env = Environment(
            loader=FileSystemLoader(template_path.parent),
            autoescape=True,  # XSS protection
        )
        self._template = env.get_template(template_path.name)

    def format(self, report: TruthfulnessReport) -> str:
        return self._template.render(report=report)

    def file_extension(self) -> str:
        return ".html"
```

## Best Practices

!!! tip "Multiple Formatters"
    Workflows can specify multiple formatters. All will be executed and saved with appropriate file extensions.

!!! warning "XSS Protection"
    Always enable `autoescape=True` in Jinja2 environments for HTML formatters to prevent injection attacks.

!!! note "File Extensions"
    The `file_extension()` method should include the leading dot (e.g., `".csv"`, not `"csv"`).
