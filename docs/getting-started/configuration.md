# Configuration

## Environment Variables

All config via `TRUTH_*` prefix:

```bash
# Models
TRUTH_EXTRACTION_MODEL=gpt-4o-mini
TRUTH_VERIFICATION_MODELS=["gpt-4o","claude-sonnet-4-5"]

# Thresholds
TRUTH_CONFIDENCE_THRESHOLD=0.7

# Features
TRUTH_ENABLE_WEB_SEARCH=true
TRUTH_ENABLE_FILESYSTEM_SEARCH=true
TRUTH_ENABLE_HUMAN_REVIEW=false

# Human-in-the-loop
TRUTH_HUMAN_REVIEW_THRESHOLD=0.6
```

## Config File

Create `.env`:

```bash
OPENAI_API_KEY=sk-...
TRUTH_EXTRACTION_MODEL=gpt-4o-mini
TRUTH_CONFIDENCE_THRESHOLD=0.6
```

Load automatically:

```python
from truthfulness_evaluator.core.config import EvaluatorConfig

config = EvaluatorConfig()  # Reads .env
```

## Python Configuration

```python
from truthfulness_evaluator.core.config import EvaluatorConfig

config = EvaluatorConfig(
    # Models
    extraction_model="gpt-4o-mini",
    verification_models=["gpt-4o", "claude-sonnet-4-5"],
    
    # Consensus
    consensus_method="weighted",  # or "ice"
    confidence_threshold=0.7,
    
    # Evidence sources
    enable_web_search=True,
    enable_filesystem_search=True,
    max_evidence_items=5,
    
    # Human review
    enable_human_review=False,
    human_review_threshold=0.6,
    
    # Output
    output_format="json",
    include_explanations=True,
    include_model_votes=True,
)
```

## Model Selection

| Model | Use For | Cost |
|-------|---------|------|
| `gpt-4o-mini` | Extraction, fast verification | Low |
| `gpt-4o` | Primary verification | Medium |
| `claude-sonnet-4-5` | Secondary verification | Medium |
| `gpt-4o` + `claude` | High-confidence consensus | Higher |

## Consensus Methods

### Weighted Voting (Default)

```python
consensus_method="weighted"
```

Models vote, weighted by reliability. Fast, good for most cases.

### Iterative Consensus Ensemble (ICE)

```python
consensus_method="ice"
ice_max_rounds=3
```

Models critique each other's reasoning. Higher accuracy, slower.

## Confidence Thresholds

| Threshold | Behavior |
|-----------|----------|
| `0.9` | Only high-confidence verdicts |
| `0.7` | Balanced (recommended) |
| `0.5` | More claims verified, less certain |

Below threshold → `NOT_ENOUGH_INFO`

## Filesystem Search

Enable to check your codebase:

```python
enable_filesystem_search=True
```

Agent tools:
- `list_files` — Browse directories
- `read_file` — Read source files
- `grep_files` — Search for patterns
- `find_related_files` — Follow imports/links

## Web Search

Enable for external verification:

```python
enable_web_search=True
```

Uses DuckDuckGo (no API key needed).
