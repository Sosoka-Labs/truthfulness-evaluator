"""Truthfulness Evaluator - Multi-model claim verification with filesystem-aware evidence gathering."""

__version__ = "0.1.0"

from .workflows.graph import create_truthfulness_graph
from .models import Claim, VerificationResult, TruthfulnessReport

__all__ = [
    "create_truthfulness_graph",
    "Claim",
    "VerificationResult", 
    "TruthfulnessReport",
]
