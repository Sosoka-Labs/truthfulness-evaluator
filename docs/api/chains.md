# Chains

!!! warning "Legacy API"
    The chains module is being replaced by the pluggable adapter architecture. New code should use the adapter classes in `extractors/`, `gatherers/`, `verifiers/`, and `formatters/` packages instead. See the [Adapters API Reference](./adapters.md) for the modern interface.

## Claim Extraction

### SimpleClaimExtractionChain

```python
from truthfulness_evaluator.llm.chains.extraction import SimpleClaimExtractionChain

extractor = SimpleClaimExtractionChain(model="gpt-4o-mini")
claims = await extractor.extract(
    document="Python was created in 1991...",
    source_path="README.md",
    max_claims=10
)
```

**Output**: `list[Claim]`

Uses structured output (`ClaimExtractionOutput`):
```python
class ClaimExtractionOutput(BaseModel):
    claims: list[ExtractedClaim]

class ExtractedClaim(BaseModel):
    text: str
    claim_type: str  # "explicit", "implicit", "inferred"
```

### TripletExtractionChain

```python
from truthfulness_evaluator.llm.chains.extraction import TripletExtractionChain

extractor = TripletExtractionChain(model="gpt-4o-mini")
claims = await extractor.extract(document, source_path)
```

Extracts subject-relation-object triplets.

## Verification

### VerificationChain

```python
from truthfulness_evaluator.llm.chains.verification import VerificationChain

verifier = VerificationChain(model_name="gpt-4o")
result = await verifier.verify(claim, evidence)
```

**Output**: `VerificationResult`

Uses structured output (`VerificationOutput`):
```python
class VerificationOutput(BaseModel):
    verdict: str           # "SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO"
    confidence: float      # 0.0 to 1.0
    reasoning: str
    key_evidence: str | None
```

## Consensus

### ConsensusChain

```python
from truthfulness_evaluator.llm.chains.consensus import ConsensusChain

consensus = ConsensusChain(
    model_names=["gpt-4o", "gpt-4o-mini"],
    weights={"gpt-4o": 0.6, "gpt-4o-mini": 0.4},
    confidence_threshold=0.7
)

result = await consensus.verify(claim, evidence)
```

Weighted voting. Models vote, weights applied, majority wins.

### ICEConsensusChain

```python
from truthfulness_evaluator.llm.chains.consensus import ICEConsensusChain

ice = ICEConsensusChain(
    model_names=["gpt-4o", "gpt-4o-mini"],
    max_rounds=3
)

result = await ice.verify(claim, evidence)
```

Iterative Consensus Ensemble. Models critique each other over multiple rounds.

## Evidence Processing

### EvidenceProcessor

```python
from truthfulness_evaluator.llm.chains.evidence import EvidenceProcessor

processor = EvidenceProcessor(model="gpt-4o-mini")

# Analyze evidence relevance
evidence, summary = await processor.analyze_evidence(claim, evidence_list)

# Synthesize multiple pieces
synthesis = await processor.synthesize_evidence(claim, evidence_list)
```

**Output**: Analyzed evidence with scores + summary text

Uses structured output (`EvidenceAnalysisOutput`):
```python
class EvidenceAnalysisOutput(BaseModel):
    evidence_analysis: list[EvidenceAnalysisItem]
    summary: str

class EvidenceAnalysisItem(BaseModel):
    index: int
    relevance: float
    supports: bool | None
    credibility: float
    reasoning: str
```

## Custom Chains

Build your own:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Define output structure
class MyOutput(BaseModel):
    result: str
    confidence: float

# Create chain
prompt = ChatPromptTemplate.from_template("Verify: {claim}")
llm = ChatOpenAI(model="gpt-4o").with_structured_output(MyOutput)
chain = prompt | llm

# Use
result = await chain.ainvoke({"claim": "Python was created in 1991"})
```

## API Reference

### Claim Extraction

::: truthfulness_evaluator.llm.chains.extraction.SimpleClaimExtractionChain
    options:
      show_root_heading: true
      show_source: true

::: truthfulness_evaluator.llm.chains.extraction.TripletExtractionChain
    options:
      show_root_heading: true
      show_source: true

### Verification

::: truthfulness_evaluator.llm.chains.verification.VerificationChain
    options:
      show_root_heading: true
      show_source: true

### Consensus

::: truthfulness_evaluator.llm.chains.consensus.ConsensusChain
    options:
      show_root_heading: true
      show_source: true

::: truthfulness_evaluator.llm.chains.consensus.ICEConsensusChain
    options:
      show_root_heading: true
      show_source: true

### Evidence Processing

::: truthfulness_evaluator.llm.chains.evidence.EvidenceProcessor
    options:
      show_root_heading: true
      show_source: true
