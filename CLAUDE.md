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
├── __init__.py              # Root public API (re-exports strategies, models, protocols)
├── truth.py                 # Typer CLI entry point
├── py.typed                 # PEP 561 marker
├── models/                  # Pydantic domain models (pure data containers)
│   ├── types.py             # Verdict type alias
│   ├── claim.py             # Claim
│   ├── evidence.py          # Evidence
│   ├── verification.py      # VerificationResult
│   └── report.py            # TruthfulnessReport, TruthfulnessStatistics
├── core/                    # Abstractions and configuration
│   ├── config.py            # EvaluatorConfig (pydantic-settings, env-prefix TRUTH_)
│   ├── grading.py           # Grading logic (calculate_grade, build_report, is_verified)
│   ├── logging_config.py    # Logging setup
│   └── protocols.py         # Protocol interfaces (ClaimExtractor, EvidenceGatherer, ClaimVerifier, ReportFormatter)
├── llm/                     # All LangChain/LangGraph integration code
│   ├── factory.py           # Centralized LLM provider factory (create_chat_model)
│   ├── chains/              # LLM chain implementations
│   │   ├── extraction.py    # Claim extraction (SimpleClaimExtractionChain, TripletExtractionChain)
│   │   ├── verification.py  # Single-model verification with structured outputs
│   │   ├── consensus.py     # Multi-model consensus (weighted voting, ICE ensemble)
│   │   ├── evidence.py      # Evidence analysis and relevance scoring
│   │   └── internal_verification.py  # Code-doc alignment (AST, config, version checking)
│   ├── prompts/             # LLM prompt templates
│   │   ├── extraction.py    # Claim extraction prompts
│   │   ├── verification.py  # Verification prompts
│   │   └── consensus.py     # Consensus prompts
│   └── workflows/           # LangGraph state machine workflows
│       ├── graph.py         # Primary workflow (external verification)
│       ├── graph_internal.py # Internal/codebase verification workflow
│       ├── state.py         # Unified WorkflowState TypedDict
│       ├── config.py        # WorkflowConfig dataclass
│       ├── registry.py      # WorkflowRegistry (name → config mapping + plugin discovery)
│       ├── builder.py       # WorkflowBuilder (stub — Phase 3)
│       └── presets.py       # Built-in workflow presets
├── strategies/              # Protocol adapter implementations
│   ├── extractors/          # SimpleExtractor, TripletExtractor
│   ├── gatherers/           # WebSearchGatherer, FilesystemGatherer, CompositeGatherer
│   ├── verifiers/           # SingleModelVerifier, ConsensusVerifier, InternalVerifier
│   └── formatters/          # JsonFormatter, MarkdownFormatter, HtmlFormatter
├── evidence/                # Evidence gathering infrastructure
│   ├── agent.py             # Filesystem ReAct agent
│   └── tools/
│       ├── filesystem.py    # Filesystem tools (list, read, grep, find_related)
│       ├── enhanced_filesystem.py  # Chunked reading, AST search
│       └── web_search.py    # Web search + URL fetching (DuckDuckGo)
└── reporting/               # Report generation
    ├── generator.py         # Report generation (JSON, Markdown, HTML)
    └── templates/
        └── report.html.j2   # HTML report template
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
