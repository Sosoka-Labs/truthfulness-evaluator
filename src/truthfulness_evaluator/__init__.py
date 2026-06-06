"""Truthfulness Evaluator - Multi-model claim verification with filesystem-aware evidence gathering."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("truthfulness-evaluator")
except PackageNotFoundError:
    __version__ = "0.1.0"

# Legacy graph constructor
# Protocols
from truthfulness_evaluator.core.protocols import (
    ClaimExtractor,
    ClaimVerifier,
    EvidenceGatherer,
    ReportFormatter,
)

# Workflow infrastructure
from truthfulness_evaluator.llm.workflows import WorkflowConfig, WorkflowRegistry
from truthfulness_evaluator.llm.workflows.graph import create_truthfulness_graph
from truthfulness_evaluator.llm.workflows.presets import register_builtin_presets

# Domain models
from truthfulness_evaluator.models import Claim, TruthfulnessReport, VerificationResult

# Strategy adapters - Extractors
from truthfulness_evaluator.strategies.extractors import SimpleExtractor, TripletExtractor

# Strategy adapters - Formatters
from truthfulness_evaluator.strategies.formatters import (
    HtmlFormatter,
    JsonFormatter,
    MarkdownFormatter,
)

# Strategy adapters - Gatherers
from truthfulness_evaluator.strategies.gatherers import (
    CompositeGatherer,
    FilesystemGatherer,
    WebSearchGatherer,
)

# Strategy adapters - Verifiers
from truthfulness_evaluator.strategies.verifiers import (
    ConsensusVerifier,
    InternalVerifier,
    SingleModelVerifier,
)

__all__ = [
    "__version__",
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
