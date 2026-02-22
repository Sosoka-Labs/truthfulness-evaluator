# Plugins

The truthfulness evaluator supports third-party plugins via Python entry points. Plugins can register custom workflows, making them available to all users via the CLI.

## Entry Point Group

Plugins register workflows under the `truthfulness_evaluator.workflows` entry point group.

## Creating a Plugin Package

Here's the complete structure for a distributable plugin:

```
truthfulness-plugin-scientific/
├── pyproject.toml
├── README.md
└── src/
    └── truthfulness_plugin_scientific/
        ├── __init__.py
        ├── extractor.py
        ├── verifier.py
        └── workflow.py
```

### 1. Implement Custom Strategies

**extractor.py:**

```python
from truthfulness_evaluator.models import Claim
from truthfulness_evaluator.llm.factory import create_chat_model

class ScientificExtractor:
    """Extracts research claims from papers."""

    def __init__(self, model: str = "gpt-4o"):
        self._model = model

    async def extract(
        self,
        document: str,
        source_path: str,
        *,
        max_claims: int | None = None,
    ) -> list[Claim]:
        # Implementation here
        ...
```

**verifier.py:**

```python
from truthfulness_evaluator.models import Claim, Evidence, VerificationResult

class PeerReviewVerifier:
    """Verifies claims against peer-reviewed sources."""

    async def verify(
        self,
        claim: Claim,
        evidence: list[Evidence],
    ) -> VerificationResult:
        # Implementation here
        ...
```

### 2. Create Workflow Configuration

**workflow.py:**

```python
from truthfulness_evaluator.llm.workflows.config import WorkflowConfig
from truthfulness_evaluator import WebSearchGatherer
from truthfulness_evaluator import JsonFormatter, MarkdownFormatter
from .extractor import ScientificExtractor
from .verifier import PeerReviewVerifier


def create_workflow() -> WorkflowConfig:
    """Factory function for the scientific workflow."""
    return WorkflowConfig(
        name="scientific",
        description="Scientific paper verification with peer-review focus",
        extractor=ScientificExtractor(model="gpt-4o"),
        gatherers=[
            WebSearchGatherer(max_results=5),
        ],
        verifier=PeerReviewVerifier(),
        formatters=[
            JsonFormatter(indent=2),
            MarkdownFormatter(),
        ],
        max_claims=15,
    )
```

### 3. Register Entry Point

**pyproject.toml:**

```toml
[project]
name = "truthfulness-plugin-scientific"
version = "0.1.0"
description = "Scientific paper verification plugin for truthfulness-evaluator"
requires-python = ">=3.11"
dependencies = [
    "truthfulness-evaluator>=0.2.0",
]

[project.entry-points."truthfulness_evaluator.workflows"]
scientific = "truthfulness_plugin_scientific.workflow:create_workflow"
```

The entry point syntax is:

```
<workflow_name> = "<module.path>:<factory_function>"
```

- **workflow_name**: Used with `--workflow` CLI flag
- **module.path**: Import path to your module
- **factory_function**: Function that returns a `WorkflowConfig`

## Discovery and Loading

The `WorkflowRegistry` automatically discovers plugins on first access:

```python
from truthfulness_evaluator.llm.workflows.registry import WorkflowRegistry

# List all workflows (built-ins + plugins)
workflows = WorkflowRegistry.list_workflows()

# Get a plugin workflow
config = WorkflowRegistry.get("scientific")
```

Discovery happens lazily and only once per process.

## Using Plugin Workflows

Once installed, users can use your plugin workflow via the CLI:

```bash
# Install the plugin
pip install truthfulness-plugin-scientific

# Use it
truth-eval paper.md --workflow scientific --output results/
```

## Plugin Distribution

Publish your plugin to PyPI for easy installation:

```bash
# Build
python -m build

# Publish
python -m twine upload dist/*
```

Users install with:

```bash
pip install truthfulness-plugin-scientific
```

## Example Plugin: Domain-Specific Workflows

Plugins are ideal for domain-specific workflows:

- **Scientific research**: Custom extractors for methodology, results, and conclusions
- **API documentation**: Verifiers that test actual API endpoints
- **Legal documents**: Extractors tuned for statutes, case law, and citations
- **Historical texts**: Verifiers that cross-reference archival sources

## Best Practices

!!! tip "Lazy Initialization"
    Use factory functions (not module-level instances) for entry points. This allows users to load the registry without instantiating expensive resources.

!!! warning "Dependencies"
    Declare `truthfulness-evaluator` as a dependency with version constraints. Use `>=0.2.0` to ensure plugin API stability.

!!! note "Testing Plugins"
    Test your plugin by installing it in editable mode:
    ```bash
    pip install -e .
    truth-eval --list-workflows
    ```

## Debugging Plugin Discovery

If your plugin doesn't appear, check:

1. Entry point group is exactly `truthfulness_evaluator.workflows`
2. Factory function returns a `WorkflowConfig` instance
3. Package is installed in the current environment
4. Check logs for discovery errors:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```
