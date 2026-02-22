# Contributing to Truthfulness Evaluator

Thank you for your interest in contributing to the Truthfulness Evaluator project. We welcome contributions of all kinds: bug fixes, new features, documentation improvements, and more.

## Development Setup

### Prerequisites

- Python 3.11 or later
- Poetry for dependency management

### Installation

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/truthfulness-evaluator.git
   cd truthfulness-evaluator
   ```
3. Install dependencies:
   ```bash
   poetry install
   ```
4. Run tests to verify setup:
   ```bash
   poetry run pytest
   ```

### Environment Configuration

Copy `.env.example` to `.env` and configure required API keys:
- `OPENAI_API_KEY` (required)
- `ANTHROPIC_API_KEY` (optional, for multi-model consensus)

All configuration uses the `TRUTH_` environment prefix.

## Code Style

We enforce strict code quality standards to maintain readability and consistency.

### Formatting and Linting

- **Black** formatter with 100 character line length
- **Ruff** linter (rules: E, F, I, N, W, UP, B, C4, SIM)
- **mypy** strict mode for type checking

Run all checks before committing:
```bash
poetry run black src/ tests/
poetry run ruff check src/ tests/
poetry run mypy src/
```

### Code Conventions

- Use `pathlib.Path` for file operations
- Import logger via `from ..core.logging_config import get_logger`
- Use centralized LLM factory: `from ..llm import create_chat_model`
- Follow Pydantic v2 patterns for all data models

## Branch Workflow

1. **Fork** the repository
2. **Create a feature branch** from `dev` (not `main`):
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** with clear, focused commits
4. **Submit a Pull Request** targeting the `dev` branch
5. **Keep PRs focused** — one feature or fix per PR

The `main` branch contains stable releases. Active development happens on `dev`.

## Commit Messages

Follow conventional commit format for clarity and automated changelog generation:

- `feat: add new claim extraction strategy`
- `fix: resolve evidence gathering timeout (#42)`
- `docs: update API reference for verification chains`
- `refactor: simplify consensus voting logic`
- `test: add integration tests for workflow registry`
- `chore: upgrade LangChain dependencies`

**Guidelines:**
- Keep subject lines under 72 characters
- Use imperative mood ("add feature" not "added feature")
- Reference issue numbers when applicable
- Provide context in the commit body for complex changes

## Testing

All contributions should include appropriate tests.

### Running Tests

```bash
poetry run pytest                    # Run all tests
poetry run pytest tests/unit/        # Run unit tests only
poetry run pytest -v                 # Verbose output
poetry run pytest -k "test_name"     # Run specific test
```

### Test Guidelines

- Use `pytest` with `pytest-asyncio` (auto mode enabled)
- Add tests for new features and bug fixes
- Ensure all existing tests pass before submitting
- Mark slow or integration tests appropriately:
  ```python
  @pytest.mark.slow
  @pytest.mark.integration
  ```
- Mock external API calls in unit tests

### Test Structure

- `tests/unit/` — Fast, isolated unit tests
- `tests/integration/` — Integration tests (may require API keys)
- Follow existing test patterns and naming conventions

## Reporting Issues

Found a bug or have a feature request? Please use GitHub Issues.

### Bug Reports

Include the following information:
- Python version (`python --version`)
- Operating system
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Relevant logs or error messages

### Feature Requests

Describe:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered
- Whether you're willing to implement it

## Questions?

For questions about contributing, open a GitHub Discussion or reach out via the project Issues page.

Thank you for helping improve Truthfulness Evaluator!
