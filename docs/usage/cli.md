# CLI Reference

## Basic Usage

```bash
truth-eval <document> [options]
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--root-path, -r` | Root directory for filesystem search | None |
| `--output, -o` | Output file (auto-detects format from extension) | None |
| `--model, -m` | Model to use (can specify multiple) | gpt-4o |
| `--confidence, -c` | Confidence threshold | 0.7 |
| `--web-search` | Enable web search (enabled by default) | True |
| `--human-review` | Enable human-in-the-loop | False |
| `--mode` | Verification mode: external, internal, both | external |

## Examples

### Basic

```bash
truth-eval README.md
```

### With Filesystem Context

```bash
truth-eval README.md --root-path .
```

### Multi-Model

```bash
truth-eval README.md \
  --model gpt-4o \
  --model gpt-4o-mini \
  --model claude-sonnet-4-5
```

### Save Report

```bash
truth-eval README.md --output report.json
truth-eval README.md -o report.md
```

### Strict Verification

```bash
truth-eval README.md --confidence 0.9
```

### Disable Web Search

Web search is enabled by default. To run without web search, use filesystem evidence only:

```bash
truth-eval README.md --root-path . --mode internal
```

### Human Review

```bash
truth-eval README.md --human-review
```

Pauses for low-confidence claims:
```
Claim: Python requires 3.11+
Proposed: NOT_ENOUGH_INFO (40%)
Approve? (approve/correct:SUPPORTS/skip)
```

## Output Formats

### Terminal (Default)

Rich tables and panels:

```
╭────────────────────── Evaluation Summary ──────────────────────╮
│ Grade: A+                                                      │
│ Confidence: 91.7%                                              │
╰────────────────────────────────────────────────────────────────╯
```

### Markdown (Recommended)

```bash
truth-eval README.md -o report.md
```

Generates a readable report with:
- Executive summary
- Detailed claim-by-claim analysis
- Evidence sources
- Model votes

### JSON

```bash
truth-eval README.md -o report.json
```

```json
{
  "overall_grade": "A+",
  "overall_confidence": 0.917,
  "claims": [...],
  "verifications": [...],
  "statistics": {
    "total_claims": 4,
    "supported": 3,
    "refuted": 0,
    "not_enough_info": 1
  }
}
```

### HTML

```bash
truth-eval README.md -o report.html
```

Self-contained HTML with styling.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (file not found, API error, etc.) |

## Environment Variables

Override defaults:

```bash
TRUTH_EXTRACTION_MODEL=gpt-4o-mini \
TRUTH_CONFIDENCE_THRESHOLD=0.6 \
truth-eval README.md
```
