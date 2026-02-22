"""
Test suite for Phase 2 protocol adapters.

Tests verify:
- Protocol compliance
- Correct forwarding to legacy chain implementations
- Error handling and edge cases
- Preset registration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from truthfulness_evaluator.protocols import (
    ClaimExtractor,
    EvidenceGatherer,
    ClaimVerifier,
    ReportFormatter,
)
from truthfulness_evaluator.models import (
    Claim,
    Evidence,
    VerificationResult,
    TruthfulnessReport,
)
from truthfulness_evaluator.core.grading import build_report

# Adapter imports
from truthfulness_evaluator.extractors.simple import SimpleExtractor
from truthfulness_evaluator.extractors.triplet import TripletExtractor
from truthfulness_evaluator.gatherers.web import WebSearchGatherer
from truthfulness_evaluator.gatherers.filesystem import FilesystemGatherer
from truthfulness_evaluator.gatherers.composite import CompositeGatherer
from truthfulness_evaluator.verifiers.single_model import SingleModelVerifier
from truthfulness_evaluator.verifiers.consensus import ConsensusVerifier
from truthfulness_evaluator.verifiers.internal import InternalVerifier
from truthfulness_evaluator.formatters.json_fmt import JsonFormatter
from truthfulness_evaluator.formatters.markdown import MarkdownFormatter
from truthfulness_evaluator.formatters.html import HtmlFormatter

# Preset imports
from truthfulness_evaluator.workflows.registry import WorkflowRegistry
from truthfulness_evaluator.workflows.presets import register_builtin_presets


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def clean_registry():
    """Clean registry before and after each test."""
    WorkflowRegistry.reset()
    yield
    WorkflowRegistry.reset()


@pytest.fixture
def sample_claims():
    """Sample claims for testing."""
    return [
        Claim(id="c1", text="Test claim 1", source_document="test.md"),
        Claim(id="c2", text="Test claim 2", source_document="test.md"),
    ]


@pytest.fixture
def sample_evidence():
    """Sample evidence for testing."""
    return [
        Evidence(
            source="https://example.com",
            source_type="web",
            content="Test content",
            relevance_score=0.9,
        )
    ]


@pytest.fixture
def sample_verifications():
    """Sample verification results for testing."""
    return [
        VerificationResult(
            claim_id="c1",
            verdict="SUPPORTS",
            confidence=0.9,
            evidence=[],
            explanation="Test explanation",
            model_votes={"gpt-4o": "SUPPORTS"},
        )
    ]


@pytest.fixture
def sample_report(sample_claims, sample_verifications):
    """Sample truthfulness report for testing."""
    return build_report(
        source_document="test.md",
        claims=sample_claims,
        verifications=sample_verifications,
    )


# =============================================================================
# 1. Protocol Compliance Tests
# =============================================================================


@pytest.mark.parametrize(
    "adapter_class,protocol_class,init_kwargs",
    [
        (SimpleExtractor, ClaimExtractor, {}),
        (TripletExtractor, ClaimExtractor, {}),
        (WebSearchGatherer, EvidenceGatherer, {}),
        (FilesystemGatherer, EvidenceGatherer, {}),
        (CompositeGatherer, EvidenceGatherer, {"gatherers": []}),
        (SingleModelVerifier, ClaimVerifier, {}),
        (
            ConsensusVerifier,
            ClaimVerifier,
            {"models": ["gpt-4o", "claude-3-5-sonnet-20241022"]},
        ),
        (InternalVerifier, ClaimVerifier, {"root_path": "/tmp"}),
        (JsonFormatter, ReportFormatter, {}),
        (MarkdownFormatter, ReportFormatter, {}),
        (HtmlFormatter, ReportFormatter, {}),
    ],
)
def test_protocol_compliance(adapter_class, protocol_class, init_kwargs):
    """Test that all adapters satisfy their respective protocols."""
    adapter = adapter_class(**init_kwargs)
    assert isinstance(adapter, protocol_class)


# =============================================================================
# 2. Extractor Forwarding Tests
# =============================================================================


@pytest.mark.asyncio
async def test_simple_extractor_forwarding():
    """Test SimpleExtractor forwards arguments correctly to legacy chain."""
    mock_chain = AsyncMock()
    mock_claims = [
        Claim(id="c1", text="Test claim", source_document="test.md"),
    ]
    mock_chain.extract.return_value = mock_claims

    with patch(
        "truthfulness_evaluator.extractors.simple.SimpleClaimExtractionChain",
        return_value=mock_chain,
    ):
        extractor = SimpleExtractor()
        result = await extractor.extract(
            document="Test document content",
            source_path="test.md",
            max_claims=5,
        )

        mock_chain.extract.assert_called_once_with(
            document="Test document content",
            source_path="test.md",
            max_claims=5,
        )
        assert result == mock_claims


@pytest.mark.asyncio
async def test_triplet_extractor_forwarding():
    """Test TripletExtractor forwards arguments correctly to legacy chain."""
    mock_chain = AsyncMock()
    mock_claims = [
        Claim(id="c1", text="Test claim", source_document="test.md"),
    ]
    mock_chain.extract.return_value = mock_claims

    with patch(
        "truthfulness_evaluator.extractors.triplet.TripletExtractionChain",
        return_value=mock_chain,
    ):
        extractor = TripletExtractor()
        result = await extractor.extract(
            document="Test document content",
            source_path="test.md",
            max_claims=10,
        )

        mock_chain.extract.assert_called_once_with(
            document="Test document content",
            source_path="test.md",
            max_claims=10,
        )
        assert result == mock_claims


# =============================================================================
# 3. Gatherer Tests
# =============================================================================


# --- WebSearchGatherer Tests ---


@pytest.mark.asyncio
async def test_web_search_gatherer_normal_results():
    """Test WebSearchGatherer converts raw dicts to Evidence objects."""
    mock_gatherer = AsyncMock()
    mock_gatherer.gather_evidence.return_value = [
        {
            "source": "https://example.com/page1",
            "source_type": "web",
            "content": "A" * 10000,  # Long content to test truncation
            "relevance": 0.85,
        },
        {
            "source": "https://example.com/page2",
            "source_type": "web_search",
            "content": "Short content",
            "relevance": 0.75,
        },
    ]

    with patch(
        "truthfulness_evaluator.gatherers.web.WebEvidenceGatherer",
        return_value=mock_gatherer,
    ):
        gatherer = WebSearchGatherer()
        claim = Claim(id="c1", text="Test claim", source_document="test.md")
        result = await gatherer.gather(claim, {})

        assert len(result) == 2
        assert all(isinstance(e, Evidence) for e in result)
        assert result[0].source == "https://example.com/page1"
        assert result[0].source_type == "web"
        assert len(result[0].content) <= 1500  # Truncated
        assert result[0].relevance_score == 0.85
        assert result[1].source == "https://example.com/page2"
        assert result[1].content == "Short content"


@pytest.mark.asyncio
async def test_web_search_gatherer_error_filtering():
    """Test WebSearchGatherer filters out error results."""
    mock_gatherer = AsyncMock()
    mock_gatherer.gather_evidence.return_value = [
        {
            "source": "https://example.com/valid",
            "source_type": "web",
            "content": "Valid content",
            "relevance": 0.9,
        },
        {
            "source": "https://example.com/error",
            "error": "Failed to fetch",
            "source_type": "web",
        },
        {
            "source": "https://example.com/another-valid",
            "source_type": "web",
            "content": "Another valid",
            "relevance": 0.8,
        },
    ]

    with patch(
        "truthfulness_evaluator.gatherers.web.WebEvidenceGatherer",
        return_value=mock_gatherer,
    ):
        gatherer = WebSearchGatherer()
        claim = Claim(id="c1", text="Test claim", source_document="test.md")
        result = await gatherer.gather(claim, {})

        # Only the two valid results should remain
        assert len(result) == 2
        assert result[0].source == "https://example.com/valid"
        assert result[1].source == "https://example.com/another-valid"


@pytest.mark.asyncio
async def test_web_search_gatherer_empty_results():
    """Test WebSearchGatherer handles empty results."""
    mock_gatherer = AsyncMock()
    mock_gatherer.gather_evidence.return_value = []

    with patch(
        "truthfulness_evaluator.gatherers.web.WebEvidenceGatherer",
        return_value=mock_gatherer,
    ):
        gatherer = WebSearchGatherer()
        claim = Claim(id="c1", text="Test claim", source_document="test.md")
        result = await gatherer.gather(claim, {})

        assert result == []


# --- FilesystemGatherer Tests ---


@pytest.mark.asyncio
async def test_filesystem_gatherer_with_root_path():
    """Test FilesystemGatherer with root_path in context."""
    mock_agent = AsyncMock()
    mock_agent.search.return_value = [
        {
            "file_path": "/project/src/main.py",
            "content": "def main(): pass",
            "relevance": 0.95,
        }
    ]

    with patch(
        "truthfulness_evaluator.gatherers.filesystem.FilesystemEvidenceAgent",
        return_value=mock_agent,
    ):
        gatherer = FilesystemGatherer()
        claim = Claim(id="c1", text="Test claim", source_document="test.md")
        context = {"root_path": Path("/project")}
        result = await gatherer.gather(claim, context)

        assert len(result) == 1
        assert isinstance(result[0], Evidence)
        assert result[0].source == "/project/src/main.py"
        assert result[0].source_type == "filesystem"
        assert result[0].content == "def main(): pass"
        assert result[0].relevance_score == 0.95


@pytest.mark.asyncio
async def test_filesystem_gatherer_without_root_path():
    """Test FilesystemGatherer returns empty list when root_path missing."""
    gatherer = FilesystemGatherer()
    claim = Claim(id="c1", text="Test claim", source_document="test.md")
    result = await gatherer.gather(claim, {})

    assert result == []


# --- CompositeGatherer Tests ---


@pytest.mark.asyncio
async def test_composite_gatherer_parallel_execution():
    """Test CompositeGatherer calls all gatherers with same args."""
    # Create mock gatherers
    mock_gatherer1 = AsyncMock()
    mock_gatherer1.gather = AsyncMock(
        return_value=[
            Evidence(
                source="source1",
                source_type="web",
                content="content1",
                relevance_score=0.9,
            )
        ]
    )

    mock_gatherer2 = AsyncMock()
    mock_gatherer2.gather = AsyncMock(
        return_value=[
            Evidence(
                source="source2",
                source_type="filesystem",
                content="content2",
                relevance_score=0.8,
            )
        ]
    )

    gatherer = CompositeGatherer(gatherers=[mock_gatherer1, mock_gatherer2])
    claim = Claim(id="c1", text="Test claim", source_document="test.md")
    context = {"test_key": "test_value"}

    result = await gatherer.gather(claim, context)

    # Both gatherers should be called with same args
    mock_gatherer1.gather.assert_called_once_with(claim, context)
    mock_gatherer2.gather.assert_called_once_with(claim, context)

    # Results should be merged
    assert len(result) == 2
    assert result[0].source == "source1"
    assert result[1].source == "source2"


@pytest.mark.asyncio
async def test_composite_gatherer_deduplication():
    """Test CompositeGatherer removes duplicate sources."""
    # Create mock gatherers returning duplicate sources
    mock_gatherer1 = AsyncMock()
    mock_gatherer1.gather = AsyncMock(
        return_value=[
            Evidence(
                source="duplicate_source",
                source_type="web",
                content="content1",
                relevance_score=0.9,
            )
        ]
    )

    mock_gatherer2 = AsyncMock()
    mock_gatherer2.gather = AsyncMock(
        return_value=[
            Evidence(
                source="duplicate_source",
                source_type="web",
                content="content2_different",
                relevance_score=0.8,
            ),
            Evidence(
                source="unique_source",
                source_type="filesystem",
                content="unique",
                relevance_score=0.7,
            ),
        ]
    )

    gatherer = CompositeGatherer(gatherers=[mock_gatherer1, mock_gatherer2])
    claim = Claim(id="c1", text="Test claim", source_document="test.md")

    result = await gatherer.gather(claim, {})

    # Should have 2 results: first duplicate_source + unique_source
    assert len(result) == 2
    assert result[0].source == "duplicate_source"
    assert result[0].content == "content1"  # First one kept
    assert result[1].source == "unique_source"


@pytest.mark.asyncio
async def test_composite_gatherer_max_total_evidence():
    """Test CompositeGatherer respects max_total_evidence limit."""
    # Create mock gatherers with many results
    mock_gatherer1 = AsyncMock()
    mock_gatherer1.gather = AsyncMock(
        return_value=[
            Evidence(
                source=f"source{i}",
                source_type="web",
                content=f"content{i}",
                relevance_score=0.9 - i * 0.1,
            )
            for i in range(5)
        ]
    )

    mock_gatherer2 = AsyncMock()
    mock_gatherer2.gather = AsyncMock(
        return_value=[
            Evidence(
                source=f"source{i+5}",
                source_type="filesystem",
                content=f"content{i+5}",
                relevance_score=0.8 - i * 0.1,
            )
            for i in range(5)
        ]
    )

    gatherer = CompositeGatherer(
        gatherers=[mock_gatherer1, mock_gatherer2], max_total_evidence=3
    )
    claim = Claim(id="c1", text="Test claim", source_document="test.md")

    result = await gatherer.gather(claim, {})

    # Should be capped at 3
    assert len(result) == 3


@pytest.mark.asyncio
async def test_composite_gatherer_exception_isolation():
    """Test CompositeGatherer isolates exceptions from individual gatherers."""
    # Create one failing and one succeeding gatherer
    mock_gatherer1 = AsyncMock()
    mock_gatherer1.gather = AsyncMock(side_effect=Exception("Gatherer 1 failed"))

    mock_gatherer2 = AsyncMock()
    mock_gatherer2.gather = AsyncMock(
        return_value=[
            Evidence(
                source="source2",
                source_type="web",
                content="content2",
                relevance_score=0.8,
            )
        ]
    )

    gatherer = CompositeGatherer(gatherers=[mock_gatherer1, mock_gatherer2])
    claim = Claim(id="c1", text="Test claim", source_document="test.md")

    result = await gatherer.gather(claim, {})

    # Should still get results from gatherer2
    assert len(result) == 1
    assert result[0].source == "source2"


@pytest.mark.asyncio
async def test_composite_gatherer_empty_list():
    """Test CompositeGatherer with empty gatherer list."""
    gatherer = CompositeGatherer(gatherers=[])
    claim = Claim(id="c1", text="Test claim", source_document="test.md")

    result = await gatherer.gather(claim, {})

    assert result == []


# =============================================================================
# 4. Verifier Tests
# =============================================================================


@pytest.mark.asyncio
async def test_single_model_verifier_forwarding():
    """Test SingleModelVerifier forwards arguments correctly."""
    mock_chain = AsyncMock()
    mock_result = VerificationResult(
        claim_id="c1",
        verdict="SUPPORTS",
        confidence=0.9,
        evidence=[],
        explanation="Test",
        model_votes={"gpt-4o": "SUPPORTS"},
    )
    mock_chain.verify.return_value = mock_result

    with patch(
        "truthfulness_evaluator.verifiers.single_model.VerificationChain",
        return_value=mock_chain,
    ):
        verifier = SingleModelVerifier(model="gpt-4o")
        claim = Claim(id="c1", text="Test claim", source_document="test.md")
        evidence = [
            Evidence(
                source="test", source_type="web", content="test", relevance_score=0.9
            )
        ]

        result = await verifier.verify(claim, evidence)

        mock_chain.verify.assert_called_once_with(claim, evidence)
        assert result == mock_result


@pytest.mark.asyncio
async def test_consensus_verifier_forwarding():
    """Test ConsensusVerifier forwards constructor params correctly."""
    mock_chain = AsyncMock()
    mock_result = VerificationResult(
        claim_id="c1",
        verdict="SUPPORTS",
        confidence=0.95,
        evidence=[],
        explanation="Consensus reached",
        model_votes={"gpt-4o": "SUPPORTS", "claude-3-5-sonnet-20241022": "SUPPORTS"},
    )
    mock_chain.verify.return_value = mock_result

    with patch(
        "truthfulness_evaluator.verifiers.consensus.ConsensusChain",
        return_value=mock_chain,
    ) as mock_constructor:
        models = ["gpt-4o", "claude-3-5-sonnet-20241022"]
        weights = {"gpt-4o": 0.6, "claude-3-5-sonnet-20241022": 0.4}
        verifier = ConsensusVerifier(
            models=models, weights=weights, confidence_threshold=0.8
        )

        # Verify constructor was called with correct params
        mock_constructor.assert_called_once_with(
            model_names=models, weights=weights, confidence_threshold=0.8
        )

        claim = Claim(id="c1", text="Test claim", source_document="test.md")
        evidence = []

        result = await verifier.verify(claim, evidence)

        assert result == mock_result


@pytest.mark.asyncio
async def test_internal_verifier_external_fact_shortcircuit():
    """Test InternalVerifier short-circuits on external_fact claims."""
    mock_classifier = MagicMock()
    mock_classifier.classify = AsyncMock(return_value=MagicMock(claim_type="external_fact"))

    with patch(
        "truthfulness_evaluator.verifiers.internal.ClaimClassifier",
        return_value=mock_classifier,
    ):
        verifier = InternalVerifier(root_path="/project")
        claim = Claim(id="c1", text="The sky is blue", source_document="test.md")

        result = await verifier.verify(claim, [])

        assert result.verdict == "NOT_ENOUGH_INFO"
        assert "external_fact" in result.explanation.lower()


@pytest.mark.asyncio
async def test_internal_verifier_api_signature_delegation():
    """Test InternalVerifier delegates api_signature claims to chain."""
    mock_classifier = MagicMock()
    mock_classifier.classify = AsyncMock(return_value=MagicMock(claim_type="api_signature"))

    mock_chain = AsyncMock()
    mock_result = VerificationResult(
        claim_id="c1",
        verdict="SUPPORTS",
        confidence=0.95,
        evidence=[],
        explanation="API matches codebase",
        model_votes={"gpt-4o": "SUPPORTS"},
    )
    mock_chain.verify.return_value = mock_result

    with patch(
        "truthfulness_evaluator.verifiers.internal.ClaimClassifier",
        return_value=mock_classifier,
    ), patch(
        "truthfulness_evaluator.verifiers.internal.InternalVerificationChain",
        return_value=mock_chain,
    ):
        verifier = InternalVerifier(root_path="/project")
        claim = Claim(id="c1", text="API uses FastAPI", source_document="README.md")

        result = await verifier.verify(claim, [])

        mock_chain.verify.assert_called_once()
        assert result == mock_result


@pytest.mark.asyncio
async def test_internal_verifier_classifier_exception():
    """Test InternalVerifier returns NEI when classifier fails."""
    mock_classifier = MagicMock()
    mock_classifier.classify = AsyncMock(side_effect=Exception("Classifier error"))

    with patch(
        "truthfulness_evaluator.verifiers.internal.ClaimClassifier",
        return_value=mock_classifier,
    ):
        verifier = InternalVerifier(root_path="/project")
        claim = Claim(id="c1", text="Test claim", source_document="test.md")

        result = await verifier.verify(claim, [])

        assert result.verdict == "NOT_ENOUGH_INFO"
        assert "error" in result.explanation.lower()


# =============================================================================
# 5. Formatter Tests
# =============================================================================


def test_json_formatter(sample_report):
    """Test JsonFormatter produces valid JSON."""
    import json

    formatter = JsonFormatter()

    result = formatter.format(sample_report)

    # Should be valid JSON
    parsed = json.loads(result)
    assert "source_document" in parsed
    assert "claims" in parsed

    assert formatter.file_extension() == ".json"


def test_markdown_formatter(sample_report):
    """Test MarkdownFormatter produces markdown output."""
    formatter = MarkdownFormatter()

    result = formatter.format(sample_report)

    # Should contain markdown heading
    assert "# Truthfulness" in result or "#" in result
    assert isinstance(result, str)

    assert formatter.file_extension() == ".md"


def test_html_formatter(sample_report):
    """Test HtmlFormatter produces HTML output."""
    formatter = HtmlFormatter()

    result = formatter.format(sample_report)

    # Should contain HTML tags
    assert "<html>" in result or "<!DOCTYPE" in result or "<div" in result
    assert isinstance(result, str)

    assert formatter.file_extension() == ".html"


# =============================================================================
# 6. Preset Registration Tests
# =============================================================================


def test_register_builtin_presets_populates_registry(clean_registry):
    """Test register_builtin_presets populates registry with expected names."""
    register_builtin_presets()

    # Should have registered the built-in presets
    available = WorkflowRegistry.list_workflows()

    # Check for expected presets (based on presets.py implementation)
    expected_presets = ["external", "full", "quick"]
    for preset in expected_presets:
        assert preset in available


def test_external_preset_has_correct_adapters(clean_registry):
    """Test 'external' preset uses expected adapter types."""
    register_builtin_presets()
    config = WorkflowRegistry.get("external")
    assert isinstance(config.extractor, SimpleExtractor)
    assert len(config.gatherers) == 1
    assert isinstance(config.gatherers[0], WebSearchGatherer)
    assert isinstance(config.verifier, ConsensusVerifier)
    assert len(config.formatters) == 2
    assert isinstance(config.formatters[0], JsonFormatter)
    assert isinstance(config.formatters[1], MarkdownFormatter)


def test_full_preset_has_correct_adapters(clean_registry):
    """Test 'full' preset uses expected adapter types."""
    register_builtin_presets()
    config = WorkflowRegistry.get("full")
    assert isinstance(config.extractor, SimpleExtractor)
    assert len(config.gatherers) == 1
    assert isinstance(config.gatherers[0], CompositeGatherer)
    assert isinstance(config.verifier, ConsensusVerifier)
    assert len(config.formatters) == 3
    assert isinstance(config.formatters[0], JsonFormatter)
    assert isinstance(config.formatters[1], MarkdownFormatter)
    assert isinstance(config.formatters[2], HtmlFormatter)


def test_quick_preset_has_correct_adapters(clean_registry):
    """Test 'quick' preset uses expected adapter types."""
    register_builtin_presets()
    config = WorkflowRegistry.get("quick")
    assert isinstance(config.extractor, SimpleExtractor)
    assert len(config.gatherers) == 1
    assert isinstance(config.gatherers[0], WebSearchGatherer)
    assert isinstance(config.verifier, SingleModelVerifier)
    assert len(config.formatters) == 1
    assert isinstance(config.formatters[0], JsonFormatter)
