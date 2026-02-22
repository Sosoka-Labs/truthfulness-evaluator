# Custom Verifiers

Claim verifiers evaluate whether evidence supports, refutes, or is insufficient for a claim. The `ClaimVerifier` protocol defines the interface for pluggable verification strategies.

## Protocol Interface

```python
from typing import Protocol
from truthfulness_evaluator.models import Claim, Evidence, VerificationResult

class ClaimVerifier(Protocol):
    async def verify(
        self,
        claim: Claim,
        evidence: list[Evidence],
    ) -> VerificationResult:
        """Verify a claim against gathered evidence."""
        ...
```

## Example: Deterministic Verifier

Here's a custom verifier that uses exact string matching for simple fact verification:

```python
from truthfulness_evaluator.models import (
    Claim,
    Evidence,
    VerificationResult,
)
from truthfulness_evaluator.core.logging_config import get_logger

logger = get_logger()


class DeterministicVerifier:
    """Verifies claims using exact string matching.

    Useful for simple facts like version numbers, dates, or
    exact configuration values where fuzzy matching isn't needed.
    """

    def __init__(
        self,
        case_sensitive: bool = False,
        min_confidence: float = 0.9,
    ):
        self._case_sensitive = case_sensitive
        self._min_confidence = min_confidence

    async def verify(
        self,
        claim: Claim,
        evidence: list[Evidence],
    ) -> VerificationResult:
        """Verify claim using exact text matching."""
        claim_text = claim.text
        if not self._case_sensitive:
            claim_text = claim_text.lower()

        supporting_count = 0
        refuting_count = 0

        for item in evidence:
            content = item.content
            if not self._case_sensitive:
                content = content.lower()

            if claim_text in content:
                supporting_count += 1
            elif self._contains_negation(content, claim_text):
                refuting_count += 1

        total = supporting_count + refuting_count

        if total == 0:
            verdict = "insufficient_evidence"
            confidence = 0.0
            explanation = "No relevant evidence found for exact matching."
        elif supporting_count > refuting_count:
            verdict = "supported"
            confidence = min(
                supporting_count / max(total, 1),
                1.0,
            )
            explanation = (
                f"Claim text found in {supporting_count} evidence sources."
            )
        elif refuting_count > supporting_count:
            verdict = "refuted"
            confidence = min(
                refuting_count / max(total, 1),
                1.0,
            )
            explanation = (
                f"Contradictory evidence found in {refuting_count} sources."
            )
        else:
            verdict = "insufficient_evidence"
            confidence = 0.5
            explanation = "Evidence is contradictory and inconclusive."

        logger.info(
            f"Deterministic verification: {verdict} "
            f"({supporting_count} support, {refuting_count} refute)"
        )

        return VerificationResult(
            claim=claim,
            verdict=verdict,
            confidence=confidence,
            explanation=explanation,
            evidence_used=evidence,
        )

    @staticmethod
    def _contains_negation(content: str, claim_text: str) -> bool:
        """Check if content contains negation of claim."""
        negations = ["not", "no", "never", "false", "incorrect"]

        # Simple heuristic: negation word near claim text
        for neg in negations:
            pattern = f"{neg} {claim_text}"
            if pattern in content:
                return True

        return False
```

## Registering with WorkflowConfig

```python
from truthfulness_evaluator.llm.workflows.config import WorkflowConfig
from truthfulness_evaluator import SimpleExtractor
from truthfulness_evaluator import FilesystemGatherer
from truthfulness_evaluator import JsonFormatter

config = WorkflowConfig(
    name="deterministic",
    description="Exact string matching verification",
    extractor=SimpleExtractor(),
    gatherers=[FilesystemGatherer()],
    verifier=DeterministicVerifier(case_sensitive=False),
    formatters=[JsonFormatter()],
)
```

## Built-in Verifiers

The library provides three built-in verifiers:

- **SingleModelVerifier**: Uses one LLM for verification (fast, lower cost)
- **ConsensusVerifier**: Uses multiple LLMs with weighted voting (higher accuracy)
- **InternalVerifier**: Specialized for code-documentation alignment (AST parsing, config validation)

For most use cases, start with `SingleModelVerifier` for speed or `ConsensusVerifier` for accuracy.

## Best Practices

!!! tip "Confidence Scores"
    Return confidence scores between 0.0 and 1.0. Scores below 0.6 typically trigger human review if enabled in `WorkflowConfig`.

!!! warning "LLM Costs"
    LLM-based verifiers can be expensive at scale. Consider batching, caching, or deterministic pre-filtering for high-volume workflows.

!!! note "Verdict Types"
    Valid verdicts: `"supported"`, `"refuted"`, `"insufficient_evidence"`. The grading system uses these for final report statistics.
