# Quick Start

## Basic Evaluation

Evaluate a document:

```bash
truth-eval evaluate README.md
```

Output:
```
✓ Loaded document: README.md
📋 Extracted 4 claims

📊 Grade: A+
Confidence: 91.7%

✅ Python was created in 1991 → SUPPORTS (90%)
✅ LangGraph 1.0 released Oct 2025 → SUPPORTS (90%)
✅ OpenAI founded 2015 → SUPPORTS (90%)
⚠️  Python requires 3.11+ → NOT_ENOUGH_INFO (40%)
```

## With Filesystem Context

For code projects, search your repo for evidence:

```bash
truth-eval evaluate README.md --root-path .
```

The agent will:
- Read relevant source files
- Check `pyproject.toml` for version claims
- Search for API documentation

## Multi-Model Consensus

Use multiple models for higher confidence:

```bash
truth-eval evaluate document.md \
  --model gpt-4o \
  --model gpt-4o-mini
```

Models vote independently. Disagreements default to `NOT_ENOUGH_INFO`.

## Save Report

```bash
truth-eval evaluate README.md --output report.json
```

JSON output includes:
- Full claim text
- Evidence sources
- Model votes
- Confidence scores

## Python API

```python
import asyncio
from truthfulness_evaluator import create_truthfulness_graph
from truthfulness_evaluator.core.config import EvaluatorConfig

async def main():
    # Configure
    config = EvaluatorConfig(
        verification_models=["gpt-4o", "gpt-4o-mini"],
        enable_web_search=True,
        confidence_threshold=0.7
    )
    
    # Create graph
    graph = create_truthfulness_graph()
    
    # Evaluate
    result = await graph.ainvoke({
        "document": open("README.md").read(),
        "document_path": "README.md",
        "root_path": ".",
        "config": config.model_dump()
    })
    
    # Report
    report = result["final_report"]
    print(f"Grade: {report.overall_grade}")
    print(f"Confidence: {report.overall_confidence:.1%}")

asyncio.run(main())
```

## Next Steps

- [Configuration](configuration.md) — Environment variables and settings
- [CLI Reference](../usage/cli.md) — All command-line options
- [Python API](../usage/python-api.md) — Programmatic usage
