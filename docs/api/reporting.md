# Reporting

The reporting module provides flexible report generation in multiple formats: JSON, Markdown, and HTML.

## ReportGenerator

The `ReportGenerator` class is the main interface for converting evaluation results into human-readable reports.

```python
from truthfulness_evaluator.reporting import ReportGenerator
from truthfulness_evaluator.models import TruthfulnessReport

# Create a generator with your evaluation report
generator = ReportGenerator(report)

# Generate report in different formats
json_output = generator.to_json()
markdown_output = generator.to_markdown()
html_output = generator.to_html()

# Save to file (format auto-detected from extension)
generator.save("report.md")
generator.save("report.json")
generator.save("report.html")
```

## Output Formats

### JSON

Generates a structured JSON representation of the entire report, including all claims, verifications, evidence, and statistics.

```python
json_report = generator.to_json(indent=2)
```

### Markdown

Creates a human-readable Markdown report with:
- Executive summary with grade and confidence
- Statistics table
- Detailed claims with verdicts and evidence
- Unvalidated claims list

Perfect for documentation, email sharing, or integration with knowledge bases.

```python
markdown_report = generator.to_markdown()
```

### HTML

Generates a styled, interactive HTML report with:
- Professional styling with responsive design
- Colored grade badges (A, B, C, D, F)
- Evidence summary with relevance scores
- Model vote breakdowns
- Unvalidated claims section

Great for web integration or email distribution.

```python
html_report = generator.to_html()
```

## Quick Functions

For simple use cases, use the standalone `generate_report()` function:

```python
from truthfulness_evaluator.reporting import generate_report

# Generate report in desired format
json_str = generate_report(report, format="json")
md_str = generate_report(report, format="markdown")
html_str = generate_report(report, format="html")
```

## API Reference

::: truthfulness_evaluator.reporting.ReportGenerator
    options:
      show_root_heading: true
      show_source: true

::: truthfulness_evaluator.reporting.generate_report
    options:
      show_root_heading: true
      show_source: true
