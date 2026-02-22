"""Claim extraction strategy implementations."""

from .simple import SimpleExtractor
from .triplet import TripletExtractor

__all__ = ["SimpleExtractor", "TripletExtractor"]
