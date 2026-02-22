"""Truthfulness Evaluator - Multi-model claim verification with filesystem-aware evidence gathering."""

__version__ = "0.1.0"

# Legacy graph constructor
from .workflows.graph import create_truthfulness_graph

# Domain models
from .models import Claim, TruthfulnessReport, VerificationResult

# Protocols
from .protocols import ClaimExtractor, ClaimVerifier, EvidenceGatherer, ReportFormatter

# Strategy adapters - Extractors
from .extractors import SimpleExtractor, TripletExtractor

# Strategy adapters - Gatherers
from .gatherers import CompositeGatherer, FilesystemGatherer, WebSearchGatherer

# Strategy adapters - Verifiers
from .verifiers import ConsensusVerifier, InternalVerifier, SingleModelVerifier

# Strategy adapters - Formatters
from .formatters import HtmlFormatter, JsonFormatter, MarkdownFormatter

# Workflow infrastructure
from .workflows import WorkflowBuilder, WorkflowConfig, WorkflowRegistry
from .workflows.presets import register_builtin_presets

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
    "WorkflowBuilder",
    "WorkflowConfig",
    "WorkflowRegistry",
    "register_builtin_presets",
]
