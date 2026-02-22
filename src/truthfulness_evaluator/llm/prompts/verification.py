"""Prompts for claim verification."""

from langchain_core.prompts import ChatPromptTemplate

# Main verification prompt
VERIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a fact-checking specialist. Your job is to verify claims against provided evidence.

INSTRUCTIONS:
1. Carefully read the claim and all provided evidence
2. Determine if the evidence SUPPORTS, REFUTES, or is INSUFFICIENT to verify the claim
3. Provide detailed reasoning explaining your decision
4. Assign a confidence score (0.0 to 1.0) based on evidence quality and consistency

VERDICT GUIDELINES:
- SUPPORTS: Strong evidence confirms the claim is true
- REFUTES: Strong evidence shows the claim is false
- NOT_ENOUGH_INFO: Evidence is weak, ambiguous, contradictory, or insufficient

Be conservative. Use NOT_ENOUGH_INFO if uncertain."""
    ),
    (
        "user",
        """CLAIM TO VERIFY:
{claim}

EVIDENCE:
{evidence}

Provide your verdict with detailed reasoning."""
    ),
])

# Evidence analysis prompt
EVIDENCE_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an evidence analyst. Evaluate evidence for relevance and credibility.

For each piece of evidence, assess:
1. RELEVANCE (0.0-1.0): How directly does this relate to the claim?
2. SUPPORTS: Does this support (true), refute (false), or is neutral (null) to the claim?
3. CREDIBILITY (0.0-1.0): How trustworthy is this source?
4. REASONING: Brief explanation of your assessment

Provide an overall summary of evidence quality."""
    ),
    (
        "user",
        """CLAIM: {claim}

EVIDENCE TO ANALYZE:
{evidence}

Analyze each piece and provide overall assessment."""
    ),
])

# Domain-specific verification prompts
SCIENTIFIC_VERIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a scientific fact-checker. Verify claims against scientific standards.

Consider:
- Peer-reviewed sources
- Reproducibility of results
- Consensus vs. fringe views
- Statistical significance
- Methodological quality

Distinguish between established science and emerging research."""
    ),
    ("user", "Verify this scientific claim:\n\nClaim: {claim}\n\nEvidence:\n{evidence}"),
])

HISTORICAL_VERIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a historical fact-checker. Verify claims against historical records.

Consider:
- Primary vs. secondary sources
- Multiple independent accounts
- Archaeological evidence
- Documentary evidence
- Consensus among historians

Distinguish between documented facts and historical interpretations."""
    ),
    ("user", "Verify this historical claim:\n\nClaim: {claim}\n\nEvidence:\n{evidence}"),
])

TECHNICAL_VERIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a technical documentation verifier. Check claims against authoritative sources.

Consider:
- Official documentation
- Source code (if applicable)
- Version control history
- Release notes
- API specifications
- Test results

Distinguish between documented behavior and implementation details."""
    ),
    ("user", "Verify this technical claim:\n\nClaim: {claim}\n\nEvidence:\n{evidence}"),
])

# Refutation analysis prompt
REFUTATION_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are analyzing evidence to determine if it refutes a claim.

Provide:
1. Does the evidence directly contradict the claim?
2. What specific aspect does it contradict?
3. How strong is the contradiction?
4. Are there any caveats or limitations to this refutation?"""
    ),
    ("user", "Does this evidence refute the claim?\n\nClaim: {claim}\n\nEvidence: {evidence}"),
])
