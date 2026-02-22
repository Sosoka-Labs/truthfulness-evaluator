"""Evidence gathering strategy implementations."""

from .composite import CompositeGatherer
from .filesystem import FilesystemGatherer
from .web import WebSearchGatherer

__all__ = ["CompositeGatherer", "FilesystemGatherer", "WebSearchGatherer"]
