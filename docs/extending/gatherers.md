# Custom Gatherers

Evidence gatherers search for information that supports or refutes claims. The `EvidenceGatherer` protocol defines the interface for pluggable gathering strategies.

## Protocol Interface

```python
from typing import Any, Protocol
from truthfulness_evaluator.models import Claim, Evidence

class EvidenceGatherer(Protocol):
    async def gather(
        self,
        claim: Claim,
        context: dict[str, Any],
    ) -> list[Evidence]:
        """Gather evidence for a claim."""
        ...
```

The `context` dict contains workflow-level state like `root_path`, configuration, and shared data.

## Example: API Gatherer

Here's a custom gatherer that queries a REST API for evidence:

```python
import httpx
from truthfulness_evaluator.models import Claim, Evidence
from truthfulness_evaluator.core.logging_config import get_logger
from typing import Any

logger = get_logger()


class APIGatherer:
    """Gathers evidence from a REST API endpoint."""

    def __init__(
        self,
        api_url: str,
        api_key: str | None = None,
        max_results: int = 3,
    ):
        self._api_url = api_url
        self._api_key = api_key
        self._max_results = max_results

    async def gather(self, claim: Claim, context: dict[str, Any]) -> list[Evidence]:
        """Query API for evidence related to the claim."""
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        params = {
            "query": claim.text,
            "limit": self._max_results,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self._api_url,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

            evidence = []
            for item in data.get("results", []):
                evidence.append(
                    Evidence(
                        source=item.get("source", self._api_url),
                        source_type="api",
                        content=item.get("content", ""),
                        relevance_score=item.get("score", 0.5),
                        supports_claim=None,  # Verifier determines this
                    )
                )

            logger.info(f"API gatherer found {len(evidence)} evidence items")
            return evidence

        except httpx.HTTPError as e:
            logger.error(f"API request failed: {e}")
            return []
```

## Combining Gatherers

Use `CompositeGatherer` to run multiple evidence sources in parallel:

```python
from truthfulness_evaluator import (
    WebSearchGatherer,
    FilesystemGatherer,
    CompositeGatherer,
)

# Combine web search, filesystem, and custom API
composite = CompositeGatherer(
    gatherers=[
        WebSearchGatherer(max_results=3),
        FilesystemGatherer(),
        APIGatherer(api_url="https://api.example.com/search"),
    ],
    max_total_evidence=10,
    deduplicate=True,
)
```

The composite gatherer runs all sources concurrently and combines results, removing duplicates and ranking by relevance score.

## Registering with WorkflowConfig

```python
from truthfulness_evaluator.llm.workflows.config import WorkflowConfig
from truthfulness_evaluator import SimpleExtractor
from truthfulness_evaluator import ConsensusVerifier
from truthfulness_evaluator import MarkdownFormatter

config = WorkflowConfig(
    name="api-verification",
    description="Uses custom API for evidence gathering",
    extractor=SimpleExtractor(),
    gatherers=[
        APIGatherer(api_url="https://api.example.com/search"),
        WebSearchGatherer(max_results=2),  # Fallback
    ],
    verifier=ConsensusVerifier(),
    formatters=[MarkdownFormatter()],
)
```

## Best Practices

!!! tip "Error Handling"
    Always handle network errors gracefully and return empty lists rather than raising exceptions. This prevents one failed gatherer from breaking the entire pipeline.

!!! note "Context Usage"
    The `context` dict contains shared workflow state. Use it to access `root_path` for filesystem operations or store intermediate results.

!!! warning "Rate Limiting"
    Implement rate limiting and retry logic for external API calls to avoid service disruptions.
