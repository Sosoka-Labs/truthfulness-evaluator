# Installation

## Requirements

- Python 3.11+
- OpenAI API key (or Anthropic for multi-model)
- Typer 0.24+ (CLI framework)

## Install

```bash
pip install truthfulness-evaluator
```

Or with Poetry:

```bash
poetry add truthfulness-evaluator
```

## Set API Keys

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."  # Optional, for multi-model
```

Or use a `.env` file:

```bash
cat > .env << EOF
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
EOF
```

## Verify Installation

```bash
truth-eval --version
```

Should output: `Truthfulness Evaluator v0.1.0`

## Optional Dependencies

Web search is enabled by default using `duckduckgo-search` (bundled with the package).

For development:

```bash
pip install truthfulness-evaluator[dev]
```

Note: `refchecker` is optional and NOT required. The tool works without it by falling back to LLM-based extraction.

## Troubleshooting

### ImportError: No module named 'refchecker'

RefChecker is optional and NOT required. The tool automatically falls back to LLM-based extraction. You can safely ignore this warning.

If you want to use triplet extraction:

```bash
pip install refchecker  # Optional, for triplet extraction
```

### DuckDuckGo search not working

```bash
pip install -U duckduckgo-search
```

### Rate limits

Use cheaper models for extraction:

```bash
export TRUTH_EXTRACTION_MODEL=gpt-4o-mini
```
