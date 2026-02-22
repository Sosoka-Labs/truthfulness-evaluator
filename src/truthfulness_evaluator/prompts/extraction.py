"""Prompts for claim extraction."""

from langchain_core.prompts import ChatPromptTemplate

# Simple claim extraction - extracts natural language claims
CLAIM_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a claim extraction specialist. Your job is to identify and extract factual claims from the provided text.

A factual claim is a statement that can be objectively verified as true or false. Extract claims that:
- Make assertions about facts, dates, numbers, or properties
- Can be verified through evidence
- Are not opinions, predictions, or subjective statements

For each claim, provide:
1. The exact claim text
2. The claim type: "explicit" (directly stated), "implicit" (inferred), or "inferred" (requires reasoning)

Return your response as a structured list of claims."""
    ),
    (
        "user",
        """Extract all factual claims from the following text:

{text}

Identify claims that can be objectively verified."""
    ),
])

# Triplet extraction - extracts subject-relation-object triplets
TRIPLET_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a knowledge extraction specialist. Extract factual claims as structured triplets.

For each factual claim, identify:
- subject: What or who the claim is about
- relation: What is being claimed (verb or relationship)
- object: The value, fact, or target of the claim
- context: Surrounding text for context (optional)

Example:
Text: "Python was created in 1991 by Guido van Rossum."
Triplet: subject="Python", relation="was created in", object="1991", context="by Guido van Rossum"

Only extract objectively verifiable facts. Skip opinions, predictions, and subjective statements."""
    ),
    (
        "user",
        """Extract knowledge triplets from:

{text}

Return structured triplets with subject, relation, object, and optional context."""
    ),
])

# Domain-specific extraction prompts
SCIENTIFIC_CLAIM_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a scientific claim extraction specialist. Focus on:
- Quantitative claims (numbers, measurements, statistics)
- Causal relationships
- Experimental results
- Scientific consensus statements

Extract claims that can be verified against scientific literature."""
    ),
    ("user", "Extract scientific claims from:\n\n{text}"),
])

HISTORICAL_CLAIM_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a historical claim extraction specialist. Focus on:
- Dates and timelines
- Historical events and figures
- Causal claims about historical events
- Documented facts vs. interpretations

Extract claims that can be verified against historical records."""
    ),
    ("user", "Extract historical claims from:\n\n{text}"),
])

TECHNICAL_CLAIM_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a technical documentation specialist. Focus on:
- Version numbers and release dates
- Technical specifications
- API behavior claims
- Compatibility statements
- Performance claims

Extract claims that can be verified against documentation or code."""
    ),
    ("user", "Extract technical claims from:\n\n{text}"),
])
