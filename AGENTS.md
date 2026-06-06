# AGENTS.md

Compact repo guide for OpenCode. High-signal facts only — if an agent would not guess it, it stays.

## Project Overview

Truthfulness Evaluator — Python CLI and library for multi-model claim verification with filesystem-aware evidence gathering. Uses LangGraph, LangChain, Pydantic v2. Target: Python 3.11+.

## Package Layout

- `src/truthfulness_evaluator/` — main package
  - `truth.py` — CLI entry point (`truth-eval` command)
  - `core/` — protocols, config, logging, grading
  - `models/` — Pydantic domain models (Claim, TruthfulnessReport, etc.)
  - `llm/` — LangGraph workflows, graph constructors, LLM factory
  - `strategies/` — pluggable adapters: extractors, gatherers, verifiers, formatters
  - `evidence/` — evidence gathering utilities
  - `reporting/` — report generation
- `tests/` — pytest suite (no `unit/` or `integration/` subdirs; tests are flat in `tests/`)
- `docs/` — MkDocs documentation source

## Environment & Setup

- **Package manager:** Poetry. Always use `poetry install`, not `pip install -e .`.
- **Install docs dependencies:** `poetry install --with docs`
- **Required env vars:** `OPENAI_API_KEY` (required to run anything real). `ANTHROPIC_API_KEY` optional for multi-model consensus.
- **Config prefix:** `TRUTH_` (e.g., `TRUTH_CLAIM_EXTRACTION_MODEL`, `TRUTH_CONFIDENCE_THRESHOLD`).
- **Copy `.env.example` to `.env`** for local development.
- **CLI respects `.env`:** `get_config()` loads `.env` first; CLI flags override only explicitly provided values. The `--model`, `--confidence`, `--web-search/--no-web-search`, and `--human-review/--no-human-review` flags all default to `None` (use `.env` value) rather than hardcoded defaults.

## Development Commands

- **Run tests:** `poetry run pytest -m "not e2e" --tb=short`
- **Run single test:** `poetry run pytest tests/test_something.py::test_name -v`
- **Format:** `poetry run black src/ tests/`
- **Lint:** `poetry run ruff check src/ tests/`
- **Type check:** `poetry run mypy src/`
- **Docs dev server:** `poetry run mkdocs serve` (or `mkdocs serve` if mkdocs is available globally)
- **Build docs:** `poetry run mkdocs build --strict`

## Toolchain Config

| Tool | Config location | Key facts |
|------|-----------------|-----------|
| Black | `pyproject.toml` [tool.black] | line-length = 100, target py311 |
| Ruff | `pyproject.toml` [tool.ruff] | line-length = 100, rules: E,F,I,N,W,UP,B,C4,SIM; ignores E501,B008 |
| mypy | `pyproject.toml` [tool.mypy] | strict = true, python_version = 3.11 |
| pytest | `pyproject.toml` [tool.pytest.ini_options] | asyncio_mode = auto, testpaths = ["tests"], markers: e2e, slow |

## CI / Git Workflow

- **CI triggers:** pushes and PRs to `main` and `develop`.
- **CI job order:** lint (Ruff) → format check (Black) → tests (pytest excluding e2e).
- **Branch model:** `main` = stable releases; `develop` = active development. Feature branches branch from `develop` and PRs target `develop`. Releases are merged from `develop` → `main` via PR.
- **Merging workflow:** New work → feature branch → PR to `develop` → PR `develop` → `main` for release → tag `vX.Y.Z` → fast-forward `develop` to `main` so both branches align.
- **No release branches:** Releases are cut by PRing `develop` directly to `main`. Do not create `release/*` branches.
- **Conventional commits:** `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- **AI code review:** All PRs trigger `Sosoka-Labs/.github/.github/workflows/ai-code-review.yml@main` via `OPENAI_API_KEY` secret.
- **Docs deploy:** `mkdocs build --strict` → GitHub Pages on every push to `main` that touches `docs/**`, `mkdocs.yml`, or `src/**`.

## Testing Notes

- **E2E tests** are marked `@pytest.mark.e2e` and require real API keys. CI excludes them with `-m "not e2e"`. Do not run E2E tests in CI or without valid keys.
- **Slow tests** are marked `@pytest.mark.slow` ( > 5 seconds).
- **Mock external API calls** in unit tests.
- **pytest-asyncio** is in auto mode; `async` tests do not need explicit decorators.

## Code Conventions

- **File operations:** Use `pathlib.Path`, never `os.path`.
- **Logger:** Import via `from ..core.logging_config import get_logger`.
- **LLM factory:** Use `from ..llm import create_chat_model` (centralized, never instantiate providers directly).
- **Models:** All data models are Pydantic v2.
- **Type hints:** `py.typed` is present; mypy strict mode is enforced.
- **Line length:** 100 characters for both Black and Ruff.

## Key Entry Points

- **CLI script:** `poetry run truth-eval README.md` (or `poetry run python -m truthfulness_evaluator.truth`)
- **Graph constructors:** `create_truthfulness_graph()` and `create_internal_verification_graph()` in `src/truthfulness_evaluator/llm/workflows/`
- **Main module exports:** `src/truthfulness_evaluator/__init__.py` exposes all public APIs.

## Version & Releases

- **Version source of truth:** `pyproject.toml` `[tool.poetry] version`.
- **Dynamic `__version__`:** `src/truthfulness_evaluator/__init__.py` reads from `pyproject.toml` via `importlib.metadata`.
- **Bump process:** `poetry version [patch|minor|major]` → update `CHANGELOG.md` with release date → tag `vX.Y.Z` → merge `develop` → `main` via PR.
- **Changelog:** `CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/) format. Every PR should update the `[Unreleased]` section.

## Operational Notes

- **Generated files to ignore:** `site/` (MkDocs build), `llm_memory/` (LLM working memory), `CLAUDE.md` (local agent scratch), `*.html` (generated reports).
- **No JSON manifest:** `pyproject.toml` is the single source of truth for deps and scripts.
- **Docs theme:** MkDocs Material, with Python docstring handlers via `mkdocstrings`.
