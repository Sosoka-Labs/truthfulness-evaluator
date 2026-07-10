"""Claim extraction strategy implementations."""

from .sentence_selection import SentenceSelectionExtractor
from .simple import SimpleExtractor
from .triplet import TripletExtractor

__all__ = ["SimpleExtractor", "TripletExtractor", "SentenceSelectionExtractor"]
