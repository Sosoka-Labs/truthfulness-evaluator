"""Built-in workflow presets."""

from ...strategies.extractors import SimpleExtractor
from ...strategies.formatters import HtmlFormatter, JsonFormatter, MarkdownFormatter
from ...strategies.gatherers import CompositeGatherer, FilesystemGatherer, WebSearchGatherer
from ...strategies.verifiers import ConsensusVerifier, InternalVerifier, SingleModelVerifier
from .config import WorkflowConfig
from .registry import WorkflowRegistry


def register_builtin_presets() -> None:
    """Register all built-in workflow presets."""

    # External verification: web search + multi-model consensus
    WorkflowRegistry.register(
        "external",
        WorkflowConfig(
            name="external",
            description="Verify claims using web search and multi-model consensus.",
            extractor=SimpleExtractor(),
            gatherers=[WebSearchGatherer()],
            verifier=ConsensusVerifier(models=["gpt-4o", "claude-sonnet-4-5"]),
            formatters=[JsonFormatter(), MarkdownFormatter()],
        ),
    )

    # Full verification: web + filesystem + multi-model consensus
    WorkflowRegistry.register(
        "full",
        WorkflowConfig(
            name="full",
            description="Comprehensive verification using web and filesystem evidence.",
            extractor=SimpleExtractor(),
            gatherers=[
                CompositeGatherer([WebSearchGatherer(), FilesystemGatherer()])
            ],
            verifier=ConsensusVerifier(models=["gpt-4o", "claude-sonnet-4-5"]),
            formatters=[JsonFormatter(), MarkdownFormatter(), HtmlFormatter()],
        ),
    )

    # Quick verification: single model + limited web search
    WorkflowRegistry.register(
        "quick",
        WorkflowConfig(
            name="quick",
            description="Fast single-model verification with web search.",
            extractor=SimpleExtractor(),
            gatherers=[WebSearchGatherer(max_results=2)],
            verifier=SingleModelVerifier(model="gpt-4o-mini"),
            formatters=[JsonFormatter()],
        ),
    )


def create_internal_config(root_path: str) -> WorkflowConfig:
    """Create a workflow config for internal/codebase verification."""
    return WorkflowConfig(
        name="internal",
        description="Verify documentation claims against codebase implementation.",
        extractor=SimpleExtractor(),
        gatherers=[FilesystemGatherer()],
        verifier=InternalVerifier(root_path=root_path),
        formatters=[JsonFormatter(), MarkdownFormatter()],
    )
