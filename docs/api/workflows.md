# Workflows

The workflow layer orchestrates the pluggable pipeline by composing extractors, gatherers, verifiers, and formatters into a complete evaluation workflow.

---

## WorkflowConfig

::: truthfulness_evaluator.llm.workflows.config.WorkflowConfig
    options:
      show_root_heading: true
      show_source: true

**Usage Example**:

```python
from truthfulness_evaluator.llm.workflows.config import WorkflowConfig
from truthfulness_evaluator import SimpleExtractor
from truthfulness_evaluator import WebSearchGatherer
from truthfulness_evaluator import ConsensusVerifier
from truthfulness_evaluator import MarkdownFormatter

config = WorkflowConfig(
    extractor=SimpleExtractor(),
    gatherer=WebSearchGatherer(max_results=5),
    verifier=ConsensusVerifier(model_names=["gpt-4o", "claude-3-5-sonnet-20241022"]),
    formatter=MarkdownFormatter()
)
```

---

## WorkflowRegistry

::: truthfulness_evaluator.llm.workflows.registry.WorkflowRegistry
    options:
      show_root_heading: true
      show_source: true

**Usage Example**:

```python
from truthfulness_evaluator.llm.workflows.registry import WorkflowRegistry

registry = WorkflowRegistry()

# Get a preset workflow
config = registry.get_workflow("external")

# List all available workflows
workflows = registry.list_workflows()
print(workflows)  # ["external", "full", "quick", "internal"]
```

---

## WorkflowState

::: truthfulness_evaluator.llm.workflows.state.WorkflowState
    options:
      show_root_heading: true
      show_source: true

**Usage Note**: `WorkflowState` is the unified state TypedDict used by LangGraph workflows. It tracks the document, extracted claims, evidence, verification results, and final report throughout the pipeline.

---

## Presets

The `workflows.presets` module provides pre-configured workflows for common use cases:

| Preset | Description | Extractor | Gatherer | Verifier | Formatter |
|--------|-------------|-----------|----------|----------|-----------|
| `external` | Web-based verification with multi-model consensus | Simple | WebSearch | Consensus (3 models) | Markdown |
| `full` | Comprehensive verification with web + filesystem | Simple | Composite (web + filesystem) | Consensus (3 models) | Markdown |
| `quick` | Fast single-model verification | Simple | WebSearch (limited) | Single model | Markdown |
| `internal` | Code-documentation alignment | Simple | Filesystem | Internal (AST/config) | Markdown |

**Usage Example**:

```python
from truthfulness_evaluator.llm.workflows.presets import create_external_config

config = create_external_config()
```

For the internal preset, you must provide the codebase root path:

```python
from truthfulness_evaluator.llm.workflows.presets import create_internal_config

config = create_internal_config(root_path="/path/to/project")
```
