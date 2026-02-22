"""Command-line interface for truthfulness evaluator."""

import asyncio
import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ..workflows.graph import create_truthfulness_graph
from ..workflows.graph_internal import create_internal_verification_graph
from ..core.config import EvaluatorConfig
from ..reporting import ReportGenerator

app = typer.Typer(help="Truthfulness Evaluator - Verify claims in documents")
console = Console()


def load_document(path: str) -> str:
    """Load document from file."""
    file_path = Path(path)
    if not file_path.exists():
        raise typer.BadParameter(f"File not found: {path}")
    
    return file_path.read_text(encoding='utf-8')


def display_report(report):
    """Display report in rich format."""
    # Summary panel
    summary = Panel(
        f"[bold]Grade:[/bold] {report.overall_grade}\n"
        f"[bold]Confidence:[/bold] {report.overall_confidence:.1%}\n"
        f"[bold]Summary:[/bold] {report.summary}",
        title="Evaluation Summary",
        box=box.ROUNDED
    )
    console.print(summary)
    
    # Statistics table
    stats = report.statistics
    table = Table(title="Statistics", box=box.SIMPLE)
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")
    table.add_column("Percentage", style="green")
    
    total = stats.total_claims
    if total > 0:
        table.add_row("Total Claims", str(total), "100%")
        table.add_row("Supported", str(stats.supported), f"{stats.supported/total:.1%}")
        table.add_row("Refuted", str(stats.refuted), f"{stats.refuted/total:.1%}")
        table.add_row("Not Enough Info", str(stats.not_enough_info), f"{stats.not_enough_info/total:.1%}")
        table.add_row("Verification Rate", "", f"{stats.verification_rate:.1%}")
    
    console.print(table)
    
    # Claims table
    claims_table = Table(title="Claim Verifications", box=box.SIMPLE)
    claims_table.add_column("#", style="dim")
    claims_table.add_column("Claim", style="cyan", max_width=50)
    claims_table.add_column("Verdict", style="bold")
    claims_table.add_column("Confidence", style="green")
    
    verdict_colors = {
        "SUPPORTS": "green",
        "REFUTES": "red",
        "NOT_ENOUGH_INFO": "yellow",
        "UNVERIFIABLE": "dim"
    }
    
    for i, verification in enumerate(report.verifications, 1):
        claim = next((c for c in report.claims if c.id == verification.claim_id), None)
        if claim:
            color = verdict_colors.get(verification.verdict, "white")
            claims_table.add_row(
                str(i),
                claim.text[:50] + "..." if len(claim.text) > 50 else claim.text,
                f"[{color}]{verification.verdict}[/{color}]",
                f"{verification.confidence:.0%}"
            )
    
    console.print(claims_table)


@app.command()
def evaluate(
    document: str = typer.Argument(..., help="Path to document to evaluate"),
    root_path: str = typer.Option(None, "--root-path", "-r", help="Root path for filesystem evidence search"),
    output: str = typer.Option(None, "--output", "-o", help="Output file for JSON report"),
    web_search: bool = typer.Option(True, "--web-search/--no-web-search", help="Enable web search"),
    models: list[str] = typer.Option(["gpt-4o"], "--model", "-m", help="Models to use for verification (can specify multiple)"),
    confidence: float = typer.Option(0.7, "--confidence", "-c", help="Confidence threshold"),
    human_review: bool = typer.Option(False, "--human-review", "-h", help="Enable human-in-the-loop for low confidence"),
    mode: str = typer.Option("external", "--mode", help="Verification mode: external, internal, or both"),
):
    """Evaluate truthfulness of claims in a document."""
    
    async def run():
        # Load document
        try:
            content = load_document(document)
            console.print(f"[green]✓[/green] Loaded document: {document}")
        except Exception as e:
            console.print(f"[red]✗[/red] Error loading document: {e}")
            raise typer.Exit(1)
        
        # Create config
        config = EvaluatorConfig(
            verification_models=list(models) if models else ["gpt-4o"],
            enable_web_search=web_search and mode in ["external", "both"],
            enable_filesystem_search=root_path is not None,
            confidence_threshold=confidence,
            enable_human_review=human_review
        )
        
        # Create appropriate graph based on mode
        if mode == "external":
            graph = create_truthfulness_graph()
        else:
            graph = create_internal_verification_graph()
        
        # Run evaluation
        console.print(f"[blue]ℹ[/blue] Starting evaluation (mode: {mode})...")
        
        try:
            # Build state based on mode
            if mode == "external":
                state = {
                    "document": content,
                    "document_path": document,
                    "root_path": root_path,
                    "claims": [],
                    "current_claim_index": 0,
                    "verifications": [],
                    "evidence_cache": {},
                    "config": config.model_dump(),
                    "final_report": None
                }
            else:
                state = {
                    "document": content,
                    "document_path": document,
                    "root_path": root_path,
                    "claims": [],
                    "current_claim_index": 0,
                    "verifications": [],
                    "evidence_cache": {},
                    "config": config.model_dump(),
                    "final_report": None,
                    "verification_mode": mode,
                    "classifications": {}
                }
            
            result = await graph.ainvoke(
                state,
                config={"configurable": {"thread_id": "eval_001"}}
            )
            
            report = result["final_report"]
            
            # Display results
            console.print()
            display_report(report)
            
            # Save to file if requested
            if output:
                output_path = Path(output)
                generator = ReportGenerator(report)
                generator.save(str(output_path))
                console.print(f"\n[green]✓[/green] Report saved to: {output}")
            
        except Exception as e:
            console.print(f"[red]✗[/red] Evaluation failed: {e}")
            raise typer.Exit(1)
    
    asyncio.run(run())


@app.command()
def version():
    """Show version information."""
    from .. import __version__
    console.print(f"Truthfulness Evaluator v{__version__}")


def main():
    """Entry point."""
    app()


# Export app for poetry script
__all__ = ["app"]
