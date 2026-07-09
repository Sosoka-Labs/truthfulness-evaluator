# Configuration

## Environment Variables

All config via `TRUTH_*` prefix:

```bash
# Models
TRUTH_CLAIM_EXTRACTION_MODEL=gpt-4o-mini
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

## API Keys

Set keys in `.env` or export them directly:

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (for multi-model consensus)
ANTHROPIC_API_KEY=sk-ant-...
FIREWORKS_API_KEY=fw-...
```

All keys are also loaded via `TRUTH_*` prefix (e.g., `TRUTH_OPENAI_API_KEY`).

## Config File

Create `.env` in the project root:

```bash
OPENAI_API_KEY=sk-...
TRUTH_CLAIM_EXTRACTION_MODEL=gpt-4o-mini
TRUTH_CONFIDENCE_THRESHOLD=0.6
TRUTH_VERIFICATION_MODELS=["gpt-4o","claude-sonnet-4-5"]
```

Load automatically (both CLI and Python API):

```python
from truthfulness_evaluator.core.config import get_config

config = get_config()  # Reads .env
```

### CLI Override

CLI flags override `.env` values. Omit a flag to use the `.env` value:

```bash
# .env
TRUTH_VERIFICATION_MODELS=["accounts/fireworks/models/llama-v3-8b-instruct"]
TRUTH_CONFIDENCE_THRESHOLD=0.9

# Uses .env models and confidence
truth-eval evaluate README.md

# Overrides only confidence
truth-eval evaluate README.md --confidence 0.7
```

## Python Configuration

```python
from truthfulness_evaluator.core.config import EvaluatorConfig

config = EvaluatorConfig(
    # Models
    claim_extraction_model="gpt-4o-mini",
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
| `accounts/fireworks/...` | Cost-effective verification | Low |
| `gpt-4o` + `claude` | High-confidence consensus | Higher |

## Providers

The provider is inferred from the **model name** (see `llm/factory.py`):

| Provider | Name must contain | Client | Key |
|----------|-------------------|--------|-----|
| OpenAI | `gpt`, `o1`, `o3`, `o4` | `ChatOpenAI` | `OPENAI_API_KEY` |
| Anthropic | `claude`, `anthropic` | `ChatAnthropic` | `ANTHROPIC_API_KEY` |
| Fireworks | `accounts/fireworks` | `ChatFireworks` | `FIREWORKS_API_KEY` |
| OpenAI-compatible | *(pass `base_url`)* | `ChatOpenAI` | — |

Keys are read from `.env` automatically (loaded into the environment on import;
existing environment variables win). A bare model alias like `kimi-k2` will not
route — Fireworks models **must** use their full `accounts/fireworks/models/...`
path.

### Fireworks Multi-Model Consensus

Fireworks hosts several strong open models behind one API key, which makes a
diverse consensus panel cheap to assemble. Verified working end to end
(extraction, structured verdicts, and weighted voting) with:

| Model | Fireworks ID |
|-------|--------------|
| GLM 5.1 | `accounts/fireworks/models/glm-5p1` |
| Kimi K2 | `accounts/fireworks/models/kimi-k2p6` |
| DeepSeek V4 Pro | `accounts/fireworks/models/deepseek-v4-pro` |

**`.env` — three different LLMs voting:**

```bash
FIREWORKS_API_KEY=fw-...

TRUTH_CLAIM_EXTRACTION_MODEL=accounts/fireworks/models/kimi-k2p6
TRUTH_VERIFICATION_MODELS=["accounts/fireworks/models/glm-5p1","accounts/fireworks/models/kimi-k2p6","accounts/fireworks/models/deepseek-v4-pro"]
TRUTH_CONFIDENCE_THRESHOLD=0.5
```

```bash
truth-eval evaluate README.md
```

**Python:**

```python
from truthfulness_evaluator.core.config import EvaluatorConfig

FIREWORKS = "accounts/fireworks/models"
config = EvaluatorConfig(
    claim_extraction_model=f"{FIREWORKS}/kimi-k2p6",
    verification_models=[
        f"{FIREWORKS}/glm-5p1",
        f"{FIREWORKS}/kimi-k2p6",
        f"{FIREWORKS}/deepseek-v4-pro",
    ],
    confidence_threshold=0.5,
)
```

Each model's individual vote is preserved in the report's `model_votes`
(enabled by `include_model_votes=True`). Providers can be mixed freely — e.g.
`["gpt-4o", "claude-sonnet-4-5", "accounts/fireworks/models/deepseek-v4-pro"]` —
since routing is per model name.

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
