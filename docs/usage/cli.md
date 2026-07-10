# CLI Reference

## Basic Usage

```bash
truth-eval evaluate <document> [options]
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--root-path, -r` | Root directory for filesystem search | None |
| `--output, -o` | Output file (auto-detects format from extension) | None |
| `--model, -m` | Model to use (can specify multiple) | `.env` or `gpt-4o` |
| `--confidence, -c` | Confidence threshold | `.env` or `0.7` |
| `--web-search` / `--no-web-search` | Enable/disable web search | `.env` or `True` |
| `--human-review` / `--no-human-review` | Enable human-in-the-loop | `.env` or `False` |
| `--mode` | Verification mode: external, internal, both | external |

## Examples

### Basic

```bash
truth-eval evaluate README.md
```

### With Filesystem Context

```bash
truth-eval evaluate README.md --root-path .
```

### Multi-Model

```bash
truth-eval evaluate README.md \
  --model gpt-4o \
  --model gpt-4o-mini \
  --model claude-sonnet-4-5
```

### Fireworks AI

```bash
export FIREWORKS_API_KEY="fw_..."
truth-eval evaluate README.md --model accounts/fireworks/models/llama-v3-8b-instruct
```

### Save Report

```bash
truth-eval evaluate README.md --output report.json
truth-eval evaluate README.md -o report.md
```

### Strict Verification

```bash
truth-eval evaluate README.md --confidence 0.9
```

### Disable Web Search

Web search is enabled by default. To run without web search, use filesystem evidence only:

```bash
truth-eval evaluate README.md --root-path . --mode internal
```

### Human Review

```bash
truth-eval evaluate README.md --human-review
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
truth-eval evaluate README.md -o report.md
```

Generates a readable report with:
- Executive summary
- Detailed claim-by-claim analysis
- Evidence sources
- Model votes

### JSON

```bash
truth-eval evaluate README.md -o report.json
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
truth-eval evaluate README.md -o report.html
```

Self-contained HTML with styling.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (file not found, API error, etc.) |

## Configuration File

The CLI reads `.env` automatically. CLI flags override `.env` values.

```bash
# .env
TRUTH_VERIFICATION_MODELS=["gpt-4o","claude-sonnet-4-5"]
TRUTH_CONFIDENCE_THRESHOLD=0.8
TRUTH_ENABLE_WEB_SEARCH=false

# Uses .env defaults
truth-eval evaluate README.md

# Overrides only the models
truth-eval evaluate README.md --model gpt-4o
```

### Flag Precedence

1. CLI flag (explicit) → wins
2. `.env` file value
3. Built-in default

### Boolean Flags

Use `--flag` or `--no-flag`:

```bash
# Explicitly disable web search (overrides .env)
truth-eval evaluate README.md --no-web-search

# Explicitly enable human review (overrides .env)
truth-eval evaluate README.md --human-review
```

## Environment Variables

Override defaults inline:

```bash
TRUTH_CLAIM_EXTRACTION_MODEL=gpt-4o-mini \
TRUTH_CONFIDENCE_THRESHOLD=0.6 \
truth-eval evaluate README.md
```
