"""Truthfulness Evaluator - Multi-model claim verification with filesystem-aware evidence gathering."""

__version__ = "0.1.0"

# Legacy graph constructor
# Protocols
from .core.protocols import ClaimExtractor, ClaimVerifier, EvidenceGatherer, ReportFormatter

# Workflow infrastructure
from .llm.workflows import WorkflowConfig, WorkflowRegistry
from .llm.workflows.graph import create_truthfulness_graph
from .llm.workflows.presets import register_builtin_presets

# Domain models
from .models import Claim, TruthfulnessReport, VerificationResult

# Strategy adapters - Extractors
from .strategies.extractors import SimpleExtractor, TripletExtractor

# Strategy adapters - Formatters
from .strategies.formatters import HtmlFormatter, JsonFormatter, MarkdownFormatter

# Strategy adapters - Gatherers
from .strategies.gatherers import CompositeGatherer, FilesystemGatherer, WebSearchGatherer

# Strategy adapters - Verifiers
from .strategies.verifiers import ConsensusVerifier, InternalVerifier, SingleModelVerifier

__all__ = [
    # Legacy
    "create_truthfulness_graph",
    # Domain models
    "Claim",
    "TruthfulnessReport",
    "VerificationResult",
    # Protocols
    "ClaimExtractor",
    "ClaimVerifier",
    "EvidenceGatherer",
    "ReportFormatter",
    # Extractors
    "SimpleExtractor",
    "TripletExtractor",
    # Gatherers
    "CompositeGatherer",
    "FilesystemGatherer",
    "WebSearchGatherer",
    # Verifiers
    "ConsensusVerifier",
    "InternalVerifier",
    "SingleModelVerifier",
    # Formatters
    "HtmlFormatter",
    "JsonFormatter",
    "MarkdownFormatter",
    # Workflow infrastructure
    "WorkflowConfig",
    "WorkflowRegistry",
    "register_builtin_presets",
]
