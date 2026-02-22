"""Report generation in multiple formats."""

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from ..models import TruthfulnessReport


def _format_percent(value: float) -> str:
    """Format float as percentage with no decimal places."""
    return f"{value:.0%}"


def _format_percent_1dp(value: float) -> str:
    """Format float as percentage with one decimal place."""
    return f"{value:.1%}"


def _verdict_icon(verdict: str) -> str:
    """Convert verdict to emoji icon."""
    icons = {
        "SUPPORTS": "✅",
        "REFUTES": "❌",
        "NOT_ENOUGH_INFO": "⚠️",
    }
    return icons.get(verdict, "❓")


def _verdict_badge_class(verdict: str) -> str:
    """Convert verdict to CSS badge class."""
    classes = {
        "SUPPORTS": "badge-success",
        "REFUTES": "badge-danger",
        "NOT_ENOUGH_INFO": "badge-warning",
    }
    return classes.get(verdict, "badge-warning")


def _verdict_badge_text(verdict: str) -> str:
    """Convert verdict to display text."""
    texts = {
        "SUPPORTS": "SUPPORTED",
        "REFUTES": "REFUTED",
        "NOT_ENOUGH_INFO": "NOT ENOUGH INFO",
    }
    return texts.get(verdict, verdict)


def _grade_class(grade: str | None) -> str:
    """Convert grade to CSS class."""
    if not grade:
        return "grade-f"
    return f"grade-{grade[0].lower()}"


def _filename(source: str) -> str:
    """Extract filename from path."""
    if "/" in source:
        return Path(source).name
    return source


def _setup_jinja_env() -> Environment:
    """Set up Jinja2 environment with custom filters."""
    env = Environment(
        loader=PackageLoader("truthfulness_evaluator.reporting", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )

    env.filters["format_percent"] = _format_percent
    env.filters["format_percent_1dp"] = _format_percent_1dp
    env.filters["verdict_icon"] = _verdict_icon
    env.filters["verdict_badge_class"] = _verdict_badge_class
    env.filters["verdict_badge_text"] = _verdict_badge_text
    env.filters["grade_class"] = _grade_class
    env.filters["filename"] = _filename

    return env


class ReportGenerator:
    """Generate reports in various formats."""
    
    def __init__(self, report: TruthfulnessReport):
        self.report = report
    
    def to_json(self, indent: int = 2) -> str:
        """Generate JSON report."""
        return self.report.model_dump_json(indent=indent)
    
    def to_markdown(self) -> str:
        """Generate Markdown report."""
        lines = []
        
        # Header
        lines.append("# Truthfulness Evaluation Report")
        lines.append("")
        lines.append(f"**Document:** {self.report.source_document}")
        lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| **Grade** | {self.report.overall_grade or 'N/A'} |")
        lines.append(f"| **Confidence** | {self.report.overall_confidence:.1%} |")
        lines.append(f"| **Total Claims** | {self.report.statistics.total_claims} |")
        lines.append(f"| **Supported** | {self.report.statistics.supported} |")
        lines.append(f"| **Refuted** | {self.report.statistics.refuted} |")
        lines.append(f"| **Not Enough Info** | {self.report.statistics.not_enough_info} |")
        lines.append("")
        
        if self.report.summary:
            lines.append(f"**Summary:** {self.report.summary}")
            lines.append("")
        
        # Detailed Results
        lines.append("## Detailed Results")
        lines.append("")
        
        for verification in self.report.verifications:
            claim = next(
                (c for c in self.report.claims if c.id == verification.claim_id),
                None
            )
            if not claim:
                continue
            
            # Claim header with verdict emoji
            emoji = {
                "SUPPORTS": "✅",
                "REFUTES": "❌",
                "NOT_ENOUGH_INFO": "⚠️"
            }.get(verification.verdict, "❓")
            
            lines.append(f"### {emoji} {claim.text}")
            lines.append("")
            
            # Verdict details
            lines.append(f"**Verdict:** {verification.verdict}")
            lines.append(f"**Confidence:** {verification.confidence:.1%}")
            lines.append("")
            
            # Model votes
            if verification.model_votes:
                lines.append("**Model Votes:**")
                for model, verdict in verification.model_votes.items():
                    model_short = model.split("-")[0]
                    lines.append(f"- {model_short}: {verdict}")
                lines.append("")
            
            # Evidence
            if verification.evidence:
                lines.append("**Evidence:**")
                for ev in verification.evidence[:3]:  # Top 3
                    source = Path(ev.source).name if "/" in ev.source else ev.source
                    lines.append(f"- {source} (relevance: {ev.relevance_score:.0%})")
                lines.append("")
            
            # Explanation
            if verification.explanation:
                lines.append("**Explanation:**")
                lines.append(f"> {verification.explanation[:500]}")
                if len(verification.explanation) > 500:
                    lines.append("> ...")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # Unvalidated claims
        if self.report.unvalidated_claims:
            lines.append("## Unvalidated Claims")
            lines.append("")
            for claim in self.report.unvalidated_claims:
                lines.append(f"- {claim.text}")
            lines.append("")
        
        return "\n".join(lines)
    
    def to_html(self) -> str:
        """Generate HTML report with proper styling."""
        env = _setup_jinja_env()
        template = env.get_template("report.html.j2")

        context = {
            "report": self.report,
            "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        return template.render(context)
    
    def save(self, path: str, format: str = "auto") -> None:
        """Save report to file."""
        output_path = Path(path)
        
        # Auto-detect format from extension
        if format == "auto":
            if output_path.suffix == ".json":
                format = "json"
            elif output_path.suffix in [".md", ".markdown"]:
                format = "markdown"
            elif output_path.suffix == ".html":
                format = "html"
            else:
                format = "markdown"  # Default
        
        # Generate content
        if format == "json":
            content = self.to_json()
        elif format == "html":
            content = self.to_html()
        else:  # markdown
            content = self.to_markdown()
        
        # Write file
        output_path.write_text(content, encoding='utf-8')


def generate_report(report: TruthfulnessReport, format: str = "markdown") -> str:
    """Quick report generation."""
    generator = ReportGenerator(report)
    
    if format == "json":
        return generator.to_json()
    elif format == "html":
        return generator.to_html()
    else:
        return generator.to_markdown()
