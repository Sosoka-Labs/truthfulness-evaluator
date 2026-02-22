"""LangGraph workflow with internal (codebase) verification support."""

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from ...core.config import EvaluatorConfig
from ...core.logging_config import get_logger
from ...models import Claim, Evidence, TruthfulnessReport, VerificationResult

logger = get_logger()


class InternalVerificationState(TypedDict):
    """State for internal verification graph."""

    document: str
    document_path: str
    root_path: str
    claims: list[Claim]
    current_claim_index: int
    verifications: list[VerificationResult]
    evidence_cache: dict[str, list[Evidence]]
    config: dict
    final_report: TruthfulnessReport | None
    verification_mode: str  # "external", "internal", "both"
    classifications: dict[str, Any]  # claim_id -> ClaimClassification


def get_config_from_state(state: InternalVerificationState) -> EvaluatorConfig:
    """Get config from state."""
    return EvaluatorConfig(**state.get("config", {}))


async def extract_and_classify_claims_node(state: InternalVerificationState) -> dict:
    """Extract claims and classify as external vs internal."""
    from ..chains.extraction import SimpleClaimExtractionChain
    from ..chains.internal_verification import ClaimClassifier

    config = get_config_from_state(state)

    # Extract claims
    extractor = SimpleClaimExtractionChain(model=config.extraction_model)
    claims = await extractor.extract(state["document"], state["document_path"])

    logger.info(f"Extracted {len(claims)} claims")

    # Classify claims if in "internal" or "both" mode
    if state.get("verification_mode") in ("internal", "both"):
        classifier = ClaimClassifier(model=config.extraction_model)
        classifications = {}

        for claim in claims:
            classification = await classifier.classify(claim)
            classifications[claim.id] = classification
            logger.debug(f"{claim.text[:40]}... → {classification.claim_type}")
    else:
        classifications = {}

    return {
        "claims": claims,
        "current_claim_index": 0,
        "verifications": [],
        "evidence_cache": {},
        "classifications": classifications,
    }


async def verify_claim_node(state: InternalVerificationState) -> dict:
    """Verify current claim using appropriate method."""
    config = get_config_from_state(state)

    if not state["claims"]:
        return {"verifications": [], "current_claim_index": 0}

    if state["current_claim_index"] >= len(state["claims"]):
        return {
            "verifications": state["verifications"],
            "current_claim_index": state["current_claim_index"],
        }

    claim = state["claims"][state["current_claim_index"]]
    mode = state.get("verification_mode", "external")

    logger.info(f"Verifying: {claim.text[:50]}...")

    # Determine verification strategy
    if mode == "external":
        verification = await _verify_external(claim, state, config)
    elif mode == "internal":
        verification = await _verify_internal(claim, state, config)
    else:  # both
        classification = state.get("classifications", {}).get(claim.id)
        if classification and classification.claim_type in [
            "api_signature",
            "version_requirement",
            "configuration",
            "behavioral",
        ]:
            logger.debug(f"Internal verification ({classification.claim_type})")
            verification = await _verify_internal(claim, state, config)
        else:
            logger.debug("External verification")
            verification = await _verify_external(claim, state, config)

    logger.debug(f"{verification.verdict} ({verification.confidence:.0%})")

    new_verifications = state["verifications"] + [verification]

    return {
        "verifications": new_verifications,
        "current_claim_index": state["current_claim_index"] + 1,
    }


async def _verify_external(
    claim: Claim, state: InternalVerificationState, config: EvaluatorConfig
) -> VerificationResult:
    """Verify using external sources (web search)."""
    from ..chains.consensus import ConsensusChain

    # Gather web evidence
    evidence = []
    if config.enable_web_search:
        from ...evidence.tools.web_search import WebEvidenceGatherer

        try:
            gatherer = WebEvidenceGatherer()
            web_evidence = await gatherer.gather_evidence(claim.text, max_results=2)
            for e in web_evidence:
                if "error" not in e:
                    evidence.append(
                        Evidence(
                            source=e.get("source", "web"),
                            source_type="web",
                            content=e.get("content", "")[:1000],
                            relevance_score=e.get("relevance", 0.6),
                        )
                    )
        except Exception as e:
            logger.warning(f"Web search failed: {e}")

    # Verify with consensus
    consensus = ConsensusChain(
        model_names=config.verification_models, confidence_threshold=config.confidence_threshold
    )

    return await consensus.verify(claim, evidence)


async def _verify_internal(
    claim: Claim, state: InternalVerificationState, config: EvaluatorConfig
) -> VerificationResult:
    """Verify using internal codebase."""
    from ..chains.internal_verification import ClaimClassifier, InternalVerificationChain

    if not state["root_path"]:
        return VerificationResult(
            claim_id=claim.id,
            verdict="NOT_ENOUGH_INFO",
            confidence=0.0,
            evidence=[],
            explanation="No root_path provided for internal verification",
            model_votes={},
        )

    # Classify if not already done
    classification = state.get("classifications", {}).get(claim.id)
    if not classification:
        classifier = ClaimClassifier(model=config.extraction_model)
        classification = await classifier.classify(claim)

    # Verify internally
    internal_verifier = InternalVerificationChain(
        root_path=state["root_path"], model=config.verification_models[0]  # Use first model
    )

    return await internal_verifier.verify(claim, classification)


def should_continue(state: InternalVerificationState) -> str:
    """Determine if we should process next claim or finish."""
    if state["current_claim_index"] >= len(state["claims"]):
        return "generate_report"
    return "verify_claim"


async def generate_report_node(state: InternalVerificationState) -> dict:
    """Generate final truthfulness report."""
    from ...core.grading import build_report

    verifications = state["verifications"]
    claims = state["claims"]

    report = build_report(
        source_document=state["document_path"],
        claims=claims,
        verifications=verifications,
    )

    mode = state.get("verification_mode", "external")
    logger.info(f"Report generated ({mode} mode): Grade {report.overall_grade}")

    return {"final_report": report}


def create_internal_verification_graph():
    """Create graph with internal verification support."""
    builder = StateGraph(InternalVerificationState)

    builder.add_node("extract_claims", extract_and_classify_claims_node)
    builder.add_node("verify_claim", verify_claim_node)
    builder.add_node("generate_report", generate_report_node)

    builder.add_edge(START, "extract_claims")
    builder.add_edge("extract_claims", "verify_claim")

    builder.add_conditional_edges(
        "verify_claim",
        should_continue,
        {"verify_claim": "verify_claim", "generate_report": "generate_report"},
    )

    builder.add_edge("generate_report", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)
