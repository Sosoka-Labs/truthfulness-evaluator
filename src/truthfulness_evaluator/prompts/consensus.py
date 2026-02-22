"""Prompts for consensus and synthesis."""

from langchain_core.prompts import ChatPromptTemplate

# Consensus synthesis prompt
CONSENSUS_SYNTHESIS_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are synthesizing multiple model verdicts into a final consensus.

Given multiple model votes on a claim:
1. Analyze agreement and disagreement
2. Consider confidence levels
3. Identify any edge cases or uncertainties
4. Produce a final verdict with synthesized reasoning

If models disagree, explain the points of contention and why one verdict is preferred."""
    ),
    (
        "user",
        """CLAIM: {claim}

MODEL VOTES:
{votes}

EVIDENCE SUMMARY:
{evidence_summary}

Synthesize into final verdict."""
    ),
])

# Debate/critique prompt for ICE (Iterative Consensus Ensemble)
DEBATE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are participating in a structured debate to verify a claim.

Your previous verdict: {previous_verdict}
Your confidence: {previous_confidence}

Other models have provided different verdicts. Review their reasoning and either:
1. Maintain your position with additional justification
2. Revise your position based on their arguments
3. Propose a compromise or nuanced position

Be specific about what evidence or reasoning changed your mind (if anything)."""
    ),
    (
        "user",
        """CLAIM: {claim}

OTHER MODEL VERDICTS:
{other_votes}

EVIDENCE:
{evidence}

Review and update your verdict."""
    ),
])

# Report generation prompt
REPORT_SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are generating an executive summary of a truthfulness evaluation.

Given verification results for multiple claims:
1. Summarize overall accuracy
2. Highlight any concerning patterns
3. Identify claims needing attention
4. Provide actionable recommendations

Keep the summary concise but informative."""
    ),
    (
        "user",
        """EVALUATION RESULTS:
- Total claims: {total_claims}
- Supported: {supported}
- Refuted: {refuted}
- Not enough info: {not_enough_info}
- Overall grade: {grade}
- Overall confidence: {confidence}

CLAIMS:
{claims_summary}

Generate executive summary."""
    ),
])

# Evidence synthesis prompt
EVIDENCE_SYNTHESIS_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """Synthesize multiple pieces of evidence into a coherent summary.

Consider:
- Agreement across sources
- Source credibility
- Relevance to the claim
- Any contradictions or gaps

Provide a balanced summary that captures the overall evidentiary landscape."""
    ),
    ("user", "Synthesize this evidence for the claim '{claim}':\n\n{evidence}"),
])
