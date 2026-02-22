# Truthfulness Evaluator

## Project Overview

A multi-model truthfulness evaluation tool that extracts factual claims from documents (primarily Markdown/README files) and verifies them using a combination of web search, filesystem evidence, and LLM consensus. Built on **LangChain/LangGraph 1.0+**.

**Owner:** John Sosoka
**Status:** Migrated from POC, preparing for public open-source release.

## Architecture

### Core Pipeline (LangGraph State Machine)

```
START -> extract_claims -> search_evidence -> verify_claim --+
                                                              |
                                     (loop per claim) <------+
                                                              |
                                     generate_report <--------+
                                                              |
                                                             END
```

Two graph variants:
- `graph.py` - Standard external verification (web + filesystem evidence)
- `graph_internal.py` - Code-documentation alignment verification (AST parsing, config matching)

### Module Structure

```
src/truthfulness_evaluator/
├── models.py              # Pydantic domain models (Claim, Evidence, VerificationResult, TruthfulnessReport)
├── config.py              # EvaluatorConfig (pydantic-settings, env-prefix TRUTH_)
├── graph.py               # Primary LangGraph workflow (external verification)
├── graph_internal.py      # Internal/codebase verification workflow
├── cli.py                 # Typer CLI (truth-eval command)
├── reporting.py           # Report generation (JSON, Markdown, HTML)
├── logging_config.py      # Logging setup
├── chains/
│   ├── extraction.py      # Claim extraction (SimpleClaimExtractionChain, TripletExtractionChain, RefChecker)
│   ├── verification.py    # Single-model verification with structured outputs
│   ├── consensus.py       # Multi-model consensus (weighted voting, ICE ensemble)
│   ├── evidence.py        # Evidence analysis and relevance scoring
│   └── internal_verification.py  # Code-doc alignment (AST, config, version checking)
├── agents/
│   └── evidence_agent.py  # Filesystem React agent for evidence gathering
├── tools/
│   ├── filesystem.py      # Filesystem tools (list, read, grep, find_related)
│   ├── enhanced_filesystem.py  # DeepAgent-inspired tools (chunked reading, AST search)
│   └── web_search.py      # Web search + URL fetching (DuckDuckGo)
└── prompts/
    ├── extraction.py      # Claim extraction prompts (general, scientific, historical, technical)
    ├── verification.py    # Verification prompts (general, evidence analysis, refutation)
    └── consensus.py       # Consensus synthesis, debate (ICE), report summary prompts
```

### Key Design Patterns

- **Structured outputs** via `with_structured_output()` on all LLM chains
- **Lazy LLM initialization** via `@property` pattern on chain classes
- **LangGraph 1.0+ state machines** with `StateGraph`, `START`/`END`, conditional edges
- **Human-in-the-loop** via `langgraph.types.interrupt`
- **Checkpointing** via `MemorySaver` for durable execution
- **Multi-provider LLMs**: OpenAI (`ChatOpenAI`) and Anthropic (`ChatAnthropic`)

## Tech Stack

- **Python** 3.11+
- **LangGraph** 1.0+ (state machine orchestration)
- **LangChain** 1.0+ (chains, tools, structured outputs)
- **langchain-openai** / **langchain-anthropic** (LLM providers)
- **Pydantic** v2 (models, settings)
- **pydantic-settings** (environment config)
- **Typer** (CLI)
- **Rich** (terminal output)
- **MkDocs Material** (documentation site)
- **Poetry** (dependency management)

## Development

```bash
poetry install
poetry run pytest
poetry run truth-eval README.md
```

### Environment Variables

Prefix `TRUTH_` for all config. See `.env.example`.

Required: `OPENAI_API_KEY`
Optional: `ANTHROPIC_API_KEY` (for multi-model consensus)

### Code Style

- **Line length:** 100
- **Formatter:** Black
- **Linter:** Ruff (E, F, I, N, W, UP, B, C4, SIM)
- **Type checking:** mypy (strict)
- **Tests:** pytest + pytest-asyncio (asyncio_mode = "auto")

### Testing

Tests live in `tests/`. Run with `pytest`. All async tests use `pytest-asyncio` auto mode.

### Documentation

MkDocs Material site. Config in `mkdocs.yml`. Docs in `docs/`.

```bash
mkdocs serve    # Dev server
mkdocs build    # Build site
```

## Design Notes

- Two types of truth verification: **external facts** (web search) and **implementation truth** (code-doc alignment)
- Claims are classified and routed to appropriate verification strategy
- Consensus methods: simple majority, weighted voting, ICE (Iterative Consensus Ensemble)
- The ICE ensemble is partially implemented (critique/revise rounds are stubbed)
- `evidence_agent.py` uses `langgraph.prebuilt.create_react_agent` with lazy initialization
- DeepAgent integration was explored but not adopted; patterns were adapted into `enhanced_filesystem.py`

## Remaining Work

- ICE consensus critique/revise rounds are stubs
- Integration/E2E tests requiring real LLM API keys not yet written
