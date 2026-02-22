# Basic Evaluation

## Evaluate a README

```bash
truth-eval README.md
```

Example README:
```markdown
# MyProject

A Python library for data processing.

## Requirements

- Python 3.8 or higher
- Works on Linux, macOS, and Windows

## History

Created in 2020 by Jane Doe.
```

Output:
```
📋 Extracted 3 claims

📊 Grade: B
Confidence: 75.0%

✅ Python 3.8 or higher → SUPPORTS (85%)
✅ Works on Linux, macOS, Windows → SUPPORTS (80%)
⚠️  Created in 2020 by Jane Doe → NOT_ENOUGH_INFO (60%)
```

## With Filesystem Context

```bash
truth-eval README.md --root-path .
```

Agent finds:
- `pyproject.toml` → verifies Python version requirement
- `setup.py` → verifies platform compatibility
- Git history → verifies creation date

## Multiple Documents

```bash
for doc in docs/*.md; do
    truth-eval "$doc" -o "reports/$(basename $doc .md).json"
done
```

## CI Integration

```yaml
# .github/workflows/verify.yml
name: Verify Documentation
on: [push]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install truthfulness-evaluator
      - run: truth-eval README.md --root-path . --confidence 0.8
```

## Python Script

```python
import asyncio
from truthfulness_evaluator import create_truthfulness_graph
from truthfulness_evaluator.core.config import EvaluatorConfig

async def verify_docs():
    graph = create_truthfulness_graph()
    config = EvaluatorConfig(confidence_threshold=0.8)
    
    docs = ["README.md", "API.md", "CHANGELOG.md"]
    
    for doc in docs:
        result = await graph.ainvoke({
            "document": open(doc).read(),
            "document_path": doc,
            "config": config.model_dump()
        })
        
        report = result["final_report"]
        print(f"{doc}: {report.overall_grade}")

asyncio.run(verify_docs())
```

## Common Issues

### Low Verification Rate

```bash
# Lower threshold for more claims verified
truth-eval README.md --confidence 0.5

# Or add more evidence sources
truth-eval README.md --root-path . --web-search
```

### False Positives

Increase confidence threshold:

```bash
truth-eval README.md --confidence 0.9
```

### Missing Claims

Claims may be too vague or opinion-based. Make them specific:

```markdown
❌ "Fast and easy to use"  # Opinion
✅ "Processes 10k rows/sec"  # Measurable
```
