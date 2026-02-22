# Core

The core module provides foundational utilities for configuration, LLM management, and grading logic.

---

## EvaluatorConfig

::: truthfulness_evaluator.core.config.EvaluatorConfig
    options:
      show_root_heading: true
      show_source: true

**Usage Example**:

```python
from truthfulness_evaluator.core.config import EvaluatorConfig

config = EvaluatorConfig(
    llm_provider="openai",
    llm_model="gpt-4o",
    llm_temperature=0.0,
    web_search_enabled=True,
    max_web_results=10
)
```

**Environment Variables**:

All configuration can be set via environment variables with the `TRUTH_` prefix:

```bash
export TRUTH_LLM_PROVIDER=openai
export TRUTH_LLM_MODEL=gpt-4o
export TRUTH_LLM_TEMPERATURE=0.0
export TRUTH_WEB_SEARCH_ENABLED=true
export TRUTH_MAX_WEB_RESULTS=10
```

---

## create_chat_model

::: truthfulness_evaluator.core.llm.create_chat_model
    options:
      show_root_heading: true
      show_source: true

**Usage Example**:

```python
from truthfulness_evaluator.core.llm import create_chat_model

# Use default config (from environment)
llm = create_chat_model()

# Override config
llm = create_chat_model(
    model="claude-3-5-sonnet-20241022",
    provider="anthropic",
    temperature=0.2
)
```

**Usage Note**: This is the centralized LLM factory function. All chains and adapters use this function to instantiate LLM instances, ensuring consistent configuration and provider routing.

---

## Grading

The grading module provides utilities for calculating truthfulness grades and building final reports.

::: truthfulness_evaluator.core.grading
    options:
      show_root_heading: true
      show_source: true

**Functions**:

- `calculate_grade(verified: int, total: int) -> str`: Calculate letter grade (A-F) from verification counts
- `is_verified(verdict: Verdict) -> bool`: Check if a verdict counts as verified (true or likely_true)
- `build_report(claims: list[Claim], results: list[VerificationResult]) -> TruthfulnessReport`: Build complete report with statistics

**Usage Example**:

```python
from truthfulness_evaluator.core.grading import calculate_grade, is_verified, build_report

# Calculate grade
grade = calculate_grade(verified=8, total=10)  # "B"

# Check if verified
from truthfulness_evaluator.models import Verdict
verified = is_verified("true")  # True
verified = is_verified("false")  # False

# Build report
report = build_report(claims=extracted_claims, results=verification_results)
```
