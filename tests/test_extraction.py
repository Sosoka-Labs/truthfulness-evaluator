"""Tests for claim extraction with example-block filtering.

These tests verify that fenced code blocks, inline code, and illustrative
scenarios are stripped before claim extraction, preventing false positives
where example claims are treated as real assertions about the project.

See: https://github.com/Sosoka-Labs/truthfulness-evaluator/issues/3
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from langchain_core.runnables import RunnableLambda
from truthfulness_evaluator.llm.chains.extraction import (
    SelectedSentence,
    SentenceSelectionExtractionChain,
    SentenceSelectionOutput,
    SimpleClaimExtractionChain,
    TripletExtractionChain,
    strip_example_blocks,
)


def _chain_returning(*selections: SelectedSentence) -> SentenceSelectionExtractionChain:
    """Build a chain whose LLM step is stubbed to return fixed selections.

    Injecting a RunnableLambda in place of the structured LLM exercises the real
    prompt-formatting, segmentation, validation, and Claim-building code paths
    without any network call.
    """
    chain = SentenceSelectionExtractionChain(model="gpt-4o-mini")
    output = SentenceSelectionOutput(selections=list(selections))
    chain._llm = RunnableLambda(lambda _: output)
    return chain


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


# =============================================================================
# 5. SentenceSelectionExtractionChain -- span-grounded extraction
# =============================================================================


class TestSentenceSelectionExtraction:
    """The model selects sentence indices; claim text is sliced from source.

    These tests guarantee the misquote-proof property: extracted claim text is
    always the verbatim source sentence, never the model's paraphrase.
    """

    DOC = "Python 3.11 was released in 2022. It is fast. Water boils at 100 degrees."

    @pytest.mark.asyncio
    async def test_claim_text_is_verbatim_not_paraphrase(self):
        """Claim text equals the source sentence even if the model paraphrases."""
        chain = _chain_returning(
            SelectedSentence(
                index=0,
                claim_type="explicit",
                normalized_claim="Python 3.11 came out in 2022",  # a paraphrase
            )
        )
        claims = await chain.extract(self.DOC, "README.md")

        assert len(claims) == 1
        # text is the exact source sentence, NOT the normalized paraphrase
        assert claims[0].text == "Python 3.11 was released in 2022."
        assert claims[0].normalized_text == "Python 3.11 came out in 2022"

    @pytest.mark.asyncio
    async def test_source_span_slices_back_to_text(self):
        """The populated source_span slices back to the claim text exactly."""
        chain = _chain_returning(SelectedSentence(index=2, claim_type="explicit"))
        claims = await chain.extract(self.DOC, "README.md")

        assert len(claims) == 1
        span = claims[0].source_span
        assert span is not None
        start, end = span
        assert self.DOC[start:end] == claims[0].text == "Water boils at 100 degrees."

    @pytest.mark.asyncio
    async def test_out_of_range_index_dropped(self):
        """Hallucinated indices outside the sentence list are ignored."""
        chain = _chain_returning(
            SelectedSentence(index=0, claim_type="explicit"),
            SelectedSentence(index=99, claim_type="explicit"),  # invalid
        )
        claims = await chain.extract(self.DOC, "README.md")

        assert len(claims) == 1
        assert claims[0].text == "Python 3.11 was released in 2022."

    @pytest.mark.asyncio
    async def test_duplicate_indices_collapsed(self):
        """The same sentence selected twice yields a single claim."""
        chain = _chain_returning(
            SelectedSentence(index=1, claim_type="explicit"),
            SelectedSentence(index=1, claim_type="implicit"),
        )
        claims = await chain.extract(self.DOC, "README.md")
        assert len(claims) == 1

    @pytest.mark.asyncio
    async def test_invalid_claim_type_defaults_to_explicit(self):
        """An unrecognized claim_type is normalized to 'explicit'."""
        chain = _chain_returning(SelectedSentence(index=0, claim_type="bogus"))
        claims = await chain.extract(self.DOC, "README.md")
        assert claims[0].claim_type == "explicit"

    @pytest.mark.asyncio
    async def test_max_claims_respected(self):
        """max_claims caps the number of returned claims."""
        chain = _chain_returning(
            SelectedSentence(index=0, claim_type="explicit"),
            SelectedSentence(index=1, claim_type="explicit"),
            SelectedSentence(index=2, claim_type="explicit"),
        )
        claims = await chain.extract(self.DOC, "README.md", max_claims=2)
        assert len(claims) == 2

    @pytest.mark.asyncio
    async def test_context_includes_neighbours(self):
        """Context is drawn from neighbouring sentences, not the claim itself."""
        chain = _chain_returning(SelectedSentence(index=1, claim_type="explicit"))
        claims = await chain.extract(self.DOC, "README.md")

        context = claims[0].context
        assert context is not None
        assert claims[0].text not in context
        assert "Python 3.11 was released in 2022." in context

    @pytest.mark.asyncio
    async def test_source_span_indexes_original_document(self):
        """source_span slices the ORIGINAL document, not a stripped copy.

        A fenced block precedes the claim; if spans were computed against the
        stripped text they would be shifted and would not round-trip here.
        """
        doc = (
            "Intro sentence.\n\n"
            "```python\n# default_timeout = 30\nx = 1\n```\n\n"
            "The service supports 1000 requests per second."
        )
        chain = _chain_returning(SelectedSentence(index=1, claim_type="explicit"))
        claims = await chain.extract(doc, "README.md")

        assert len(claims) == 1
        start, end = claims[0].source_span
        assert doc[start:end] == claims[0].text
        assert claims[0].text == "The service supports 1000 requests per second."

    @pytest.mark.asyncio
    async def test_example_block_claims_never_selectable(self):
        """Claims inside fenced code get no index, so they cannot be selected."""
        doc = (
            "The real timeout is 60 seconds.\n\n"
            "```python\n# default_timeout = 30\n```\n\n"
            "The API is stable."
        )
        # Index 1 refers to the second *real* sentence after stripping the fence,
        # proving the fenced claim was never enumerated.
        chain = _chain_returning(
            SelectedSentence(index=0, claim_type="explicit"),
            SelectedSentence(index=1, claim_type="explicit"),
        )
        claims = await chain.extract(doc, "README.md")

        texts = [c.text for c in claims]
        assert "The real timeout is 60 seconds." in texts
        assert "The API is stable." in texts
        assert all("default_timeout" not in t for t in texts)

    @pytest.mark.asyncio
    async def test_empty_document_returns_no_claims(self):
        chain = _chain_returning(SelectedSentence(index=0, claim_type="explicit"))
        assert await chain.extract("   \n\n  ", "README.md") == []

    @pytest.mark.asyncio
    async def test_llm_failure_returns_empty(self):
        """A failing LLM step degrades to an empty claim list, matching peers."""
        chain = SentenceSelectionExtractionChain(model="gpt-4o-mini")

        def _boom(_):
            raise RuntimeError("LLM unavailable")

        chain._llm = RunnableLambda(_boom)
        assert await chain.extract(self.DOC, "README.md") == []


class TestSentenceSelectionOnFixture:
    """End-to-end style test over the shared fixture document."""

    FIXTURE = Path(__file__).parent / "fixtures" / "sample_project_doc.md"

    @pytest.mark.asyncio
    async def test_selected_claims_are_verbatim_source_quotes(self):
        """Every extracted claim is a verbatim slice of the fixture document."""
        document = self.FIXTURE.read_text()
        # Select the four real factual sentences (indices verified against the
        # deterministic segmentation of the fixture, excluding example blocks).
        chain = _chain_returning(
            SelectedSentence(index=1, claim_type="explicit"),  # released in 2019
            SelectedSentence(index=2, claim_type="explicit"),  # Python 3.11
            SelectedSentence(index=3, claim_type="explicit"),  # timeout 60s
            SelectedSentence(index=6, claim_type="explicit"),  # batch size 100
        )
        claims = await chain.extract(document, str(self.FIXTURE))

        assert len(claims) == 4
        for claim in claims:
            # Verbatim guarantee: source_span indexes the ORIGINAL document and
            # slices back to the exact claim text.
            start, end = claim.source_span
            assert document[start:end] == claim.text
        assert claims[1].text == "It requires Python 3.11 or higher."
        # A fenced-block claim must never surface as an extracted claim.
        assert all("batch_size = 500" not in c.text for c in claims)
