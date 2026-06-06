# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Replaced all relative `..` and `...` imports with absolute `truthfulness_evaluator.*` imports throughout the codebase
- Moved inline/dynamic imports inside functions to top-of-file imports (except optional `refchecker` dependency)
- Extracted Pydantic models from `llm/chains/` into a new `llm/models/` package for better separation of concerns

## [0.1.0] - 2026-06-05

### Added

- First-class Fireworks AI LLM provider support (`langchain-fireworks`)
- `fireworks_api_key` config field with `FIREWORKS_API_KEY` env fallback
- CLI now respects `.env` configuration via `get_config()` instead of hardcoding defaults
- `--web-search/--no-web-search` and `--human-review/--no-human-review` boolean flag pairs
- Comprehensive `.env.example` with all available configuration options
- `CHANGELOG.md` and dynamic versioning via `importlib.metadata`
- `AGENTS.md` release process documentation
- README.md version badge and `.env` file mention
- Multi-model claim verification with filesystem-aware evidence gathering
- CLI (`truth-eval`) for evaluating Markdown documents
- LangGraph-based workflows with checkpointing and human-in-the-loop support
- Pluggable strategies: extractors, gatherers, verifiers, formatters
- Web search (DuckDuckGo) and filesystem evidence gathering
- Weighted consensus and ICE (Iterative Consensus Ensemble) voting
- JSON, Markdown, and HTML report generation
- MkDocs documentation site
- CI/CD with GitHub Actions (lint, format, test, docs deploy)
- AI code review on all PRs

### Changed

- Renamed `extraction_model` config field to `claim_extraction_model` (env var: `TRUTH_CLAIM_EXTRACTION_MODEL`)
- Standardized all branch references from `dev` to `develop` in documentation
- Updated CLI docs with configuration file precedence rules, Fireworks AI examples, and `.env` defaults
- Updated model selection table in docs to include Fireworks AI

### Fixed

- CLI `--model`, `--confidence`, `--web-search`, and `--human-review` flags now default to `.env` values instead of silently overriding them
- All documentation references to `TRUTH_EXTRACTION_MODEL` updated to `TRUTH_CLAIM_EXTRACTION_MODEL`

