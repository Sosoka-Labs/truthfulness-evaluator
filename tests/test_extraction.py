"""Tests for claim extraction with example-block filtering.

These tests verify that fenced code blocks, inline code, and illustrative
scenarios are stripped before claim extraction, preventing false positives
where example claims are treated as real assertions about the project.

See: https://github.com/Sosoka-Labs/truthfulness-evaluator/issues/3
"""

from unittest.mock import patch

import pytest
from truthfulness_evaluator.llm.chains.extraction import (
    SimpleClaimExtractionChain,
    TripletExtractionChain,
    strip_example_blocks,
)

# =============================================================================
# 1. strip_example_blocks() unit tests
# =============================================================================


class TestStripExampleBlocks:
    """Test the deterministic pre-processor that removes example content."""

    def test_fenced_code_block_triple_backticks(self):
        """Triple-backtick fenced blocks are removed."""
        text = """Some prose.

```python
# Default timeout is 30 seconds
default_timeout = 30
```

More prose."""
        result = strip_example_blocks(text)
        assert "Default timeout is 30 seconds" not in result
        assert "Some prose." in result
        assert "More prose." in result

    def test_fenced_code_block_tilde(self):
        """Tilde-fenced blocks are removed."""
        text = """Some prose.

~~~bash
# batch_size defaults to 100
export BATCH_SIZE=100
~~~

More prose."""
        result = strip_example_blocks(text)
        assert "batch_size defaults to 100" not in result
        assert "Some prose." in result
        assert "More prose." in result

    def test_inline_code_removed(self):
        """Inline code spans are stripped."""
        text = 'The `CONFIGURATION = "config"  # Default port is 8080` is an example.'
        result = strip_example_blocks(text)
        assert "CONFIGURATION" not in result
        assert "Default port is 8080" not in result
        assert "The" in result
        assert "is an example." in result

    def test_multiple_fenced_blocks(self):
        """Multiple fenced blocks in one document are all removed."""
        text = """Intro.

```
Claim one
```

Middle text.

```
Claim two
```

Outro."""
        result = strip_example_blocks(text)
        assert "Claim one" not in result
        assert "Claim two" not in result
        assert "Intro." in result
        assert "Middle text." in result
        assert "Outro." in result

    def test_no_blocks_unchanged(self):
        """Text without code blocks passes through unchanged."""
        text = "Python 3.11 introduced improved error messages and performance optimizations."
        result = strip_example_blocks(text)
        assert result == text

    def test_fenced_block_with_language_tag(self):
        """Fenced blocks with a language tag are removed."""
        text = """Some prose.

```yaml
# Default port is 8080
port: 8080
```

More prose."""
        result = strip_example_blocks(text)
        assert "Default port is 8080" not in result
        assert "port: 8080" not in result
        assert "Some prose." in result
        assert "More prose." in result

    def test_mixed_backticks_and_tildes(self):
        """Mixed fence styles in one document are all removed."""
        text = """Intro.

```
Backtick block
```

Middle.

~~~
Tilde block
~~~

Outro."""
        result = strip_example_blocks(text)
        assert "Backtick block" not in result
        assert "Tilde block" not in result
        assert "Intro." in result
        assert "Middle." in result
        assert "Outro." in result


# =============================================================================
# 2. SimpleClaimExtractionChain integration tests
# =============================================================================


class TestSimpleClaimExtractionChain:
    """Test that SimpleClaimExtractionChain strips example blocks before LLM call."""

    @pytest.mark.asyncio
    async def test_extracts_stripped_text(self):
        """Verify strip_example_blocks is called with the original document."""
        document = """# README

The default timeout is 60 seconds.

```python
# This is an example showing REFUTED output
# default timeout is 30 seconds
default_timeout = 30
```

Requires Python 3.11 or higher.
"""
        chain = SimpleClaimExtractionChain(model="gpt-4o-mini")
        captured_input = {}

        with (
            patch(
                "truthfulness_evaluator.llm.chains.extraction.create_chat_model",
                side_effect=RuntimeError("No LLM in unit test"),
            ),
            patch(
                "truthfulness_evaluator.llm.chains.extraction.strip_example_blocks",
                side_effect=lambda t: captured_input.update({"original": t})
                or strip_example_blocks(t),
            ),
            pytest.raises(RuntimeError, match="No LLM in unit test"),
        ):
            await chain.extract(document, "README.md")

        assert captured_input["original"] == document
        assert "default timeout is 30 seconds" in captured_input["original"]

    @pytest.mark.asyncio
    async def test_inline_code_stripped(self):
        """Verify inline code triggers strip_example_blocks."""
        document = (
            'The `CONFIGURATION = "config"  # Default port is 8080` '
            "is just an example. The real API supports GraphQL."
        )
        chain = SimpleClaimExtractionChain(model="gpt-4o-mini")
        captured_input = {}

        with (
            patch(
                "truthfulness_evaluator.llm.chains.extraction.create_chat_model",
                side_effect=RuntimeError("No LLM in unit test"),
            ),
            patch(
                "truthfulness_evaluator.llm.chains.extraction.strip_example_blocks",
                side_effect=lambda t: captured_input.update({"original": t})
                or strip_example_blocks(t),
            ),
            pytest.raises(RuntimeError, match="No LLM in unit test"),
        ):
            await chain.extract(document, "docs.md")

        assert captured_input["original"] == document
        assert "Default port is 8080" in captured_input["original"]


# =============================================================================
# 3. TripletExtractionChain integration tests
# =============================================================================


class TestTripletExtractionChain:
    """Test that TripletExtractionChain strips example blocks before LLM call."""

    @pytest.mark.asyncio
    async def test_extracts_stripped_text(self):
        """Verify strip_example_blocks is called with the original document."""
        document = """# Docs

Python was created in 1991.

```
# Example output:
# batch_size defaults to 100
batch_size = 100
```

Water boils at 100 degrees Celsius.
"""
        chain = TripletExtractionChain(model="gpt-4o-mini")
        captured_input = {}

        with (
            patch(
                "truthfulness_evaluator.llm.chains.extraction.create_chat_model",
                side_effect=RuntimeError("No LLM in unit test"),
            ),
            patch(
                "truthfulness_evaluator.llm.chains.extraction.strip_example_blocks",
                side_effect=lambda t: captured_input.update({"original": t})
                or strip_example_blocks(t),
            ),
            pytest.raises(RuntimeError, match="No LLM in unit test"),
        ):
            await chain.extract(document, "docs.md")

        assert captured_input["original"] == document
        assert "batch_size defaults to 100" in captured_input["original"]


# =============================================================================
# 4. End-to-end style test with realistic doc content
# =============================================================================


class TestRealisticDocumentFiltering:
    """Test with realistic documentation content similar to issue #3."""

    def test_internal_verification_doc(self):
        """Reproduce the internal-verification.md example from issue #3."""
        text = """## Example 2: Configuration Default Mismatch

**README.md:**
```markdown
The default timeout is 30 seconds.
```

**Actual Code (src/config.py):**
```python
DEFAULT_TIMEOUT = 60  # seconds
```

**Verification Result:**
```
❌ REFUTES (95% confidence)
   Claim: "default timeout is 30 seconds"
   📁 Evidence: src/config.py:12 (DEFAULT_TIMEOUT = 60)
```

The tool correctly identified that the documentation is outdated.
"""
        result = strip_example_blocks(text)
        # All fenced content should be gone
        assert "default timeout is 30 seconds" not in result
        assert "DEFAULT_TIMEOUT = 60" not in result
        assert "REFUTES" not in result
        # Prose should remain
        assert "Example 2: Configuration Default Mismatch" in result
        assert "The tool correctly identified" in result

    def test_filesystem_doc(self):
        """Reproduce the filesystem.md example from issue #3."""
        text = """# Filesystem Evidence

## Smart file selection based on claim type:

```python
# API claims → Search src/**/*.py
# Version claims → Check pyproject.toml, setup.py
# Config claims → Check config.py, settings.yaml
```

The batch_size defaults to 100.
"""
        result = strip_example_blocks(text)
        # Fenced code should be gone
        assert "API claims" not in result
        assert "src/**/*.py" not in result
        # But the prose claim should remain
        assert "The batch_size defaults to 100." in result
