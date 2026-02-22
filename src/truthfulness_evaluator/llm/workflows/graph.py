"""LangGraph 1.0+ workflow for truthfulness evaluation."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from typing_extensions import TypedDict

from ...core.config import EvaluatorConfig
from ...core.logging_config import get_logger
from ...models import Claim, Evidence, TruthfulnessReport, VerificationResult

logger = get_logger()


class TruthfulnessState(TypedDict):
    """State managed by the graph."""

    document: str
    document_path: str
    root_path: str | None
    claims: list[Claim]
    current_claim_index: int
    verifications: list[VerificationResult]
    evidence_cache: dict[str, list[Evidence]]  # claim_id -> evidence
    config: dict
    final_report: TruthfulnessReport | None


def get_config_from_state(state: TruthfulnessState) -> EvaluatorConfig:
    """Get config from state."""
    return EvaluatorConfig(**state.get("config", {}))


# Node implementations
async def extract_claims_node(state: TruthfulnessState) -> dict:
    """Extract claims from document."""
    from ..chains.extraction import SimpleClaimExtractionChain

    config = get_config_from_state(state)

    # Use simple extraction for now (RefChecker has dependency issues)
    extractor = SimpleClaimExtractionChain(model=config.extraction_model)

    claims = await extractor.extract(state["document"], state["document_path"])

    logger.info(f"Extracted {len(claims)} claims")

    return {"claims": claims, "current_claim_index": 0, "verifications": [], "evidence_cache": {}}


async def search_evidence_node(state: TruthfulnessState) -> dict:
    """Search for evidence for current claim."""
    config = get_config_from_state(state)

    # Check if we have claims to process
    if not state["claims"]:
        return {"evidence_cache": {}}

    if state["current_claim_index"] >= len(state["claims"]):
        return {"evidence_cache": state.get("evidence_cache", {})}

    claim = state["claims"][state["current_claim_index"]]

    logger.info(f"Searching evidence for: {claim.text[:60]}...")

    evidence = []

    # Filesystem search
    if config.enable_filesystem_search and state["root_path"]:
        from ...evidence.agent import FilesystemEvidenceAgent

        try:
            agent = FilesystemEvidenceAgent(state["root_path"])
            fs_evidence = await agent.search(claim.text)

            for e in fs_evidence:
                evidence.append(
                    Evidence(
                        source=e.get("file_path", "unknown"),
                        source_type="filesystem",
                        content=e.get("content", "")[:1000],
                        relevance_score=e.get("relevance", 0.5),
                        supports_claim=e.get("supports"),
                    )
                )

            if fs_evidence:
                logger.debug(f"Found {len(fs_evidence)} filesystem evidence items")
        except Exception as e:
            logger.warning(f"Filesystem search failed: {e}")

    # Web search
    if config.enable_web_search:
        from ...evidence.tools.web_search import WebEvidenceGatherer

        try:
            gatherer = WebEvidenceGatherer()
            web_evidence = await gatherer.gather_evidence(claim.text, max_results=3)

            logger.debug(f"Web search returned {len(web_evidence)} raw results")

            for e in web_evidence:
                if "error" not in e:
                    evidence.append(
                        Evidence(
                            source=e.get("source", "web"),
                            source_type="web",
                            content=e.get("content", "")[:1500],
                            relevance_score=e.get("relevance", 0.6),
                            supports_claim=None,  # Will be determined during verification
                        )
                    )

            if evidence:
                logger.debug(
                    f"Added {len([e for e in evidence if e.source_type == 'web'])} web evidence items"
                )
        except Exception as e:
            logger.warning(f"Web search failed: {e}")

    # Process and analyze evidence
    if evidence:
        from ..chains.evidence import EvidenceProcessor

        processor = EvidenceProcessor(model=config.extraction_model)

        try:
            evidence, analysis = await processor.analyze_evidence(claim, evidence)
            logger.debug(f"Evidence analysis: {analysis[:100]}...")
        except Exception as e:
            logger.warning(f"Evidence analysis failed: {e}")

    # Cache evidence
    evidence_cache = state.get("evidence_cache", {})
    evidence_cache[claim.id] = evidence

    logger.debug(f"Total evidence: {len(evidence)} items")

    return {"evidence_cache": evidence_cache}


async def verify_claim_node(state: TruthfulnessState) -> dict:
    """Verify current claim using consensus."""
    config = get_config_from_state(state)

    # Check if we have claims to process
    if not state["claims"]:
        return {"verifications": [], "current_claim_index": 0}

    if state["current_claim_index"] >= len(state["claims"]):
        return {
            "verifications": state["verifications"],
            "current_claim_index": state["current_claim_index"],
        }

    claim = state["claims"][state["current_claim_index"]]
    evidence = state.get("evidence_cache", {}).get(claim.id, [])

    logger.info(f"Verifying: {claim.text[:60]}...")

    from ..chains.consensus import ConsensusChain

    consensus = ConsensusChain(
        model_names=config.verification_models, confidence_threshold=config.confidence_threshold
    )

    verification = await consensus.verify(claim, evidence)

    logger.debug(f"Verdict: {verification.verdict} (confidence: {verification.confidence:.0%})")

    # Human-in-the-loop for low confidence
    if config.enable_human_review and verification.confidence < config.human_review_threshold:
        logger.info("Requesting human review...")
        human_input = interrupt(
            {
                "type": "human_review",
                "claim": claim.text,
                "proposed_verdict": verification.verdict,
                "confidence": verification.confidence,
                "evidence_count": len(evidence),
                "question": "Approve this verdict? (approve/correct:VERDICT/skip)",
            }
        )

        if human_input:
            response = human_input.get("response", "").strip().lower()

            if response.startswith("correct:"):
                new_verdict = response.split(":")[1].upper()
                if new_verdict in ["SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO"]:
                    verification.verdict = new_verdict
                    verification.confidence = 1.0
                    verification.explanation += "\n[Human-corrected]"
                    logger.info(f"Corrected to: {new_verdict}")
            elif response == "approve":
                verification.confidence = 1.0
                verification.explanation += "\n[Human-approved]"
                logger.info("Approved")

    new_verifications = state["verifications"] + [verification]

    return {
        "verifications": new_verifications,
        "current_claim_index": state["current_claim_index"] + 1,
    }


def should_continue(state: TruthfulnessState) -> str:
    """Determine if we should process next claim or finish."""
    if state["current_claim_index"] >= len(state["claims"]):
        return "generate_report"
    return "search_evidence"


async def generate_report_node(state: TruthfulnessState) -> dict:
    """Generate final truthfulness report."""
    from ...core.grading import build_report

    verifications = state["verifications"]
    claims = state["claims"]

    logger.info(f"Generating report for {len(claims)} claims...")

    report = build_report(
        source_document=state["document_path"],
        claims=claims,
        verifications=verifications,
    )

    logger.info(f"Report generated: Grade {report.overall_grade}")

    return {"final_report": report}


def create_truthfulness_graph():
    """Create and compile the truthfulness evaluation graph."""
    builder = StateGraph(TruthfulnessState)

    # Add nodes
    builder.add_node("extract_claims", extract_claims_node)
    builder.add_node("search_evidence", search_evidence_node)
    builder.add_node("verify_claim", verify_claim_node)
    builder.add_node("generate_report", generate_report_node)

    # Define edges
    builder.add_edge(START, "extract_claims")
    builder.add_edge("extract_claims", "search_evidence")
    builder.add_edge("search_evidence", "verify_claim")

    # Conditional: continue to next claim or generate report
    builder.add_conditional_edges(
        "verify_claim",
        should_continue,
        {"search_evidence": "search_evidence", "generate_report": "generate_report"},
    )

    builder.add_edge("generate_report", END)

    # Checkpointing for durability
    checkpointer = MemorySaver()

    return builder.compile(checkpointer=checkpointer)
