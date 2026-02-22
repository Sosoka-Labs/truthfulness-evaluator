"""Grading and summary logic for truthfulness reports."""

from ..models import Claim, TruthfulnessReport, TruthfulnessStatistics, VerificationResult


def is_verified(
    result: VerificationResult,
    confidence_threshold: float = 0.7,
) -> bool:
    """Whether a verification result meets the verification criteria.

    Args:
        result: The verification result to check.
        confidence_threshold: Minimum confidence to consider verified.

    Returns:
        True if verdict is SUPPORTS/REFUTES and confidence meets threshold.
    """
    return result.verdict in ("SUPPORTS", "REFUTES") and result.confidence >= confidence_threshold


def calculate_grade(
    verifications: list[VerificationResult],
    confidence_threshold: float = 0.7,
) -> str:
    """Calculate letter grade from verification results.

    Args:
        verifications: List of verification results.
        confidence_threshold: Minimum confidence to consider a claim verified.

    Returns:
        Letter grade string (A+ through F).
    """
    if not verifications:
        return "F"

    verified = [v for v in verifications if is_verified(v, confidence_threshold)]
    if not verified:
        return "F"

    support_ratio = sum(1 for v in verified if v.verdict == "SUPPORTS") / len(verified)
    confidence = sum(v.confidence for v in verified) / len(verified)

    score = round(support_ratio * confidence, 10)

    if score >= 0.9:
        return "A+"
    elif score >= 0.85:
        return "A"
    elif score >= 0.8:
        return "A-"
    elif score >= 0.75:
        return "B+"
    elif score >= 0.7:
        return "B"
    elif score >= 0.65:
        return "B-"
    elif score >= 0.6:
        return "C+"
    elif score >= 0.55:
        return "C"
    elif score >= 0.5:
        return "C-"
    elif score >= 0.4:
        return "D"
    else:
        return "F"


def calculate_statistics(
    claims: list[Claim],
    verifications: list[VerificationResult],
) -> TruthfulnessStatistics:
    """Calculate statistics from claims and verifications.

    Args:
        claims: List of claims.
        verifications: List of verification results.

    Returns:
        TruthfulnessStatistics instance.
    """
    total = len(claims)
    supported = sum(1 for v in verifications if v.verdict == "SUPPORTS")
    refuted = sum(1 for v in verifications if v.verdict == "REFUTES")
    not_enough_info = sum(1 for v in verifications if v.verdict == "NOT_ENOUGH_INFO")
    unverifiable = sum(1 for v in verifications if v.verdict == "UNVERIFIABLE")

    verified_count = supported + refuted
    verification_rate = (verified_count / total) if total > 0 else 0.0
    accuracy_score = (supported / verified_count) if verified_count > 0 else 0.0

    return TruthfulnessStatistics(
        total_claims=total,
        supported=supported,
        refuted=refuted,
        not_enough_info=not_enough_info,
        unverifiable=unverifiable,
        verification_rate=verification_rate,
        accuracy_score=accuracy_score,
    )


def generate_summary(
    grade: str,
    statistics: TruthfulnessStatistics,
) -> str:
    """Generate human-readable summary of evaluation results.

    Args:
        grade: Letter grade.
        statistics: TruthfulnessStatistics instance.

    Returns:
        Summary string.
    """
    stats = statistics

    if stats.total_claims == 0:
        return "No claims were extracted from the document."

    summary = f"Document received grade {grade}. "
    summary += f"Of {stats.total_claims} claims, "
    summary += f"{stats.supported} were supported, "
    summary += f"{stats.refuted} were refuted, and "
    summary += f"{stats.not_enough_info + stats.unverifiable} could not be verified."

    if stats.verification_rate < 0.5:
        summary += " Many claims lacked sufficient evidence for verification."
    elif stats.accuracy_score < 0.7:
        summary += " Several claims were found to be inaccurate."
    else:
        summary += " The document appears to be largely accurate."

    return summary


def build_report(
    source_document: str,
    claims: list[Claim],
    verifications: list[VerificationResult],
    *,
    confidence_threshold: float = 0.7,
    grade: str | None = None,
    summary: str | None = None,
) -> TruthfulnessReport:
    """Build a complete TruthfulnessReport with computed fields.

    This is the primary way to construct a report. It computes
    grade, statistics, confidence, and summary from the raw data.

    Args:
        source_document: Path/URL of source document.
        claims: Extracted claims.
        verifications: Verification results.
        confidence_threshold: Threshold for considering claims verified.
        grade: Override grade (if None, computed from verifications).
        summary: Override summary (if None, generated automatically).

    Returns:
        TruthfulnessReport instance.
    """
    verified_ids = {v.claim_id for v in verifications}
    unvalidated = [c for c in claims if c.id not in verified_ids]

    stats = calculate_statistics(claims, verifications)
    computed_grade = grade or calculate_grade(verifications, confidence_threshold)
    overall_confidence = (
        sum(v.confidence for v in verifications) / len(verifications) if verifications else 0.0
    )
    computed_summary = summary or generate_summary(computed_grade, stats)

    return TruthfulnessReport(
        source_document=source_document,
        overall_grade=computed_grade,
        overall_confidence=overall_confidence,
        summary=computed_summary,
        claims=claims,
        verifications=verifications,
        unvalidated_claims=unvalidated,
        statistics=stats,
    )
