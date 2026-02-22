"""Protocol implementation strategies (adapter layer)."""

from .extractors import SimpleExtractor, TripletExtractor
from .formatters import HtmlFormatter, JsonFormatter, MarkdownFormatter
from .gatherers import CompositeGatherer, FilesystemGatherer, WebSearchGatherer
from .verifiers import ConsensusVerifier, InternalVerifier, SingleModelVerifier

__all__ = [
    "SimpleExtractor",
    "TripletExtractor",
    "CompositeGatherer",
    "FilesystemGatherer",
    "WebSearchGatherer",
    "ConsensusVerifier",
    "InternalVerifier",
    "SingleModelVerifier",
    "HtmlFormatter",
    "JsonFormatter",
    "MarkdownFormatter",
]
