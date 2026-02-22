# Installation

## Requirements

- Python 3.11+
- OpenAI API key (or Anthropic for multi-model)

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

For filesystem evidence gathering:

```bash
pip install beautifulsoup4 requests
```

For development:

```bash
pip install truthfulness-evaluator[dev]
```

## Troubleshooting

### ImportError: No module named 'refchecker'

RefChecker is optional. The tool falls back to LLM-based extraction:

```bash
pip install refchecker  # Optional, for triplet extraction
```

### DuckDuckGo search not working

```bash
pip install -U ddgs
```

### Rate limits

Use cheaper models for extraction:

```bash
export TRUTH_EXTRACTION_MODEL=gpt-4o-mini
```
