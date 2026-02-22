# Custom Extractors

Claim extractors analyze document text and extract factual claims for verification. The `ClaimExtractor` protocol defines the interface for pluggable extraction strategies.

## Protocol Interface

```python
from typing import Protocol
from truthfulness_evaluator.models import Claim

class ClaimExtractor(Protocol):
    async def extract(
        self,
        document: str,
        source_path: str,
        *,
        max_claims: int | None = None,
    ) -> list[Claim]:
        """Extract claims from document text."""
        ...
```

## Example: Scientific Claim Extractor

Here's a custom extractor that focuses on extracting research claims from scientific documents:

```python
from truthfulness_evaluator.models import Claim
from truthfulness_evaluator.llm.factory import create_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel


class ClaimList(BaseModel):
    """Container for extracted claims."""
    claims: list[str]


class ScientificClaimExtractor:
    """Extracts research claims from scientific documents."""

    def __init__(self, model: str = "gpt-4o"):
        self._model_name = model
        self._parser = PydanticOutputParser(pydantic_object=ClaimList)

    async def extract(
        self,
        document: str,
        source_path: str,
        *,
        max_claims: int | None = None,
    ) -> list[Claim]:
        """Extract scientific claims from document."""
        llm = create_chat_model(self._model_name)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a scientific claim extractor. Extract factual "
             "research claims from the document. Focus on empirical findings, "
             "methodology claims, and statistical assertions."),
            ("user", "Document:\n{document}\n\n{format_instructions}")
        ])

        chain = prompt | llm | self._parser

        result = await chain.ainvoke({
            "document": document[:8000],  # Limit context window
            "format_instructions": self._parser.get_format_instructions(),
        })

        claims = []
        for idx, claim_text in enumerate(result.claims):
            if max_claims and idx >= max_claims:
                break
            claims.append(
                Claim(
                    text=claim_text,
                    source=source_path,
                    claim_type="research",
                )
            )

        return claims
```

## Registering with WorkflowConfig

To use your custom extractor in a workflow:

```python
from truthfulness_evaluator.llm.workflows.config import WorkflowConfig
from truthfulness_evaluator.llm.workflows.registry import WorkflowRegistry
from truthfulness_evaluator import WebSearchGatherer
from truthfulness_evaluator import SingleModelVerifier
from truthfulness_evaluator import JsonFormatter

# Create extractor instance
extractor = ScientificClaimExtractor(model="gpt-4o")

# Build workflow config
config = WorkflowConfig(
    name="scientific",
    description="Scientific document verification",
    extractor=extractor,
    gatherers=[WebSearchGatherer(max_results=5)],
    verifier=SingleModelVerifier(model="gpt-4o"),
    formatters=[JsonFormatter()],
    max_claims=10,
)

# Register for CLI use
WorkflowRegistry.register("scientific", config)
```

## Best Practices

!!! tip "LLM Initialization"
    Use `create_chat_model()` from `truthfulness_evaluator.llm.factory` for centralized provider management and consistent configuration.

!!! warning "Context Window Limits"
    Always truncate document input to avoid exceeding model context limits. Scientific papers can be lengthy.

!!! note "Claim Types"
    Use meaningful `claim_type` values to enable downstream routing and specialized verification strategies.
