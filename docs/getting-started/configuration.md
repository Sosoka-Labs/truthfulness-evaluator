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
    consensus_method="weighted",  # or "simple"
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

Consensus is **agreement-based**: each model in `verification_models` returns its own
verdict (`SUPPORTS` / `REFUTES` / `NOT_ENOUGH_INFO`), and `ConsensusChain` tallies those
verdicts using per-model weights (equal weights by default). The leading verdict is
committed only if there's no tie for the lead and its weighted agreement fraction meets
`confidence_threshold`; otherwise the ensemble abstains to `NOT_ENOUGH_INFO`. Per-model
votes are always recorded in the report's `model_votes`.

Each model's own self-reported confidence is **not** used for this decision — it's
recorded for reference, but the reported confidence on the final verdict is the weighted
agreement fraction itself (i.e., how strongly the models agreed), not an average of their
self-reported scores.

```python
consensus_method="weighted"  # or "simple"
```

`"weighted"` applies the `weights` mapping passed to `ConsensusChain`; `"simple"` treats
all models equally.

!!! note "`confidence_threshold` is an agreement threshold"
    With N equal-weight models, `confidence_threshold` is effectively how much agreement
    you require, not a per-model confidence cutoff. With 3 equal-weight models, a 2-out-of-3
    majority is only 0.67 agreement — a threshold of `0.7` would reject that and abstain,
    requiring unanimity. Lower the threshold (e.g. `0.6`) to accept simple majorities.

## Confidence Thresholds

| Threshold | Behavior |
|-----------|----------|
| `0.9` | Only high-confidence verdicts (near-unanimity required) |
| `0.7` | Balanced (recommended); with 3 equal-weight models, requires unanimity |
| `0.5` | Accepts simple majorities, more claims verified, less certain |

Below threshold, or on a tie for the lead verdict → `NOT_ENOUGH_INFO`

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
