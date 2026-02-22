# Models

## Claim

```python
class Claim(BaseModel):
    id: str                    # Unique identifier
    text: str                  # The claim text
    source_document: str       # Source path/URL
    source_span: tuple[int, int] | None  # Character positions
    context: str | None        # Surrounding text
    claim_type: str            # "explicit", "implicit", "inferred"
```

## Evidence

```python
class Evidence(BaseModel):
    source: str                # URL or file path
    source_type: str           # "web", "filesystem", "knowledge_base"
    content: str               # Relevant excerpt
    relevance_score: float     # 0.0 to 1.0
    supports_claim: bool | None  # True/False/None
    credibility_score: float   # 0.0 to 1.0
```

## VerificationResult

```python
class VerificationResult(BaseModel):
    claim_id: str              # Reference to claim
    verdict: str               # "SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO"
    confidence: float          # 0.0 to 1.0
    evidence: list[Evidence]   # Evidence considered
    explanation: str           # Detailed reasoning
    model_votes: dict[str, str]  # {model: verdict}
    
    @property
    def is_verified(self) -> bool:
        """True if SUPPORTS/REFUTES with confidence >= 0.7"""
```

## TruthfulnessReport

```python
class TruthfulnessReport(BaseModel):
    source_document: str
    overall_grade: str | None  # "A+", "A", "B+", etc.
    overall_confidence: float
    summary: str
    claims: list[Claim]
    verifications: list[VerificationResult]
    unvalidated_claims: list[Claim]
    statistics: TruthfulnessStatistics
    
    def calculate_grade(self) -> str:
        """Compute letter grade from results"""
```

## TruthfulnessStatistics

```python
class TruthfulnessStatistics(BaseModel):
    total_claims: int
    supported: int
    refuted: int
    not_enough_info: int
    unverifiable: int
    
    @property
    def verification_rate(self) -> float:
        """Fraction of claims verified"""
        
    @property
    def accuracy_score(self) -> float:
        """supported / (supported + refuted)"""
```

## Usage

```python
from truthfulness_evaluator.models import Claim, Evidence, VerificationResult

# Create claim
claim = Claim(
    id="claim_001",
    text="Python was created in 1991",
    source_document="README.md"
)

# Create evidence
evidence = Evidence(
    source="python.org",
    source_type="web",
    content="Python was created by Guido van Rossum...",
    relevance_score=0.95,
    supports_claim=True
)

# Create result
result = VerificationResult(
    claim_id=claim.id,
    verdict="SUPPORTS",
    confidence=0.9,
    evidence=[evidence],
    explanation="Multiple sources confirm...",
    model_votes={"gpt-4o": "SUPPORTS"}
)
```

## Serialization

All models support JSON:

```python
# To JSON
json_str = report.model_dump_json(indent=2)

# From JSON
report = TruthfulnessReport.model_validate_json(json_str)
```

## API Reference

### Claim

::: truthfulness_evaluator.models.Claim
    options:
      show_root_heading: true
      show_source: true

### Evidence

::: truthfulness_evaluator.models.Evidence
    options:
      show_root_heading: true
      show_source: true

### VerificationResult

::: truthfulness_evaluator.models.VerificationResult
    options:
      show_root_heading: true
      show_source: true

### TruthfulnessReport

::: truthfulness_evaluator.models.TruthfulnessReport
    options:
      show_root_heading: true
      show_source: true

### TruthfulnessStatistics

::: truthfulness_evaluator.models.TruthfulnessStatistics
    options:
      show_root_heading: true
      show_source: true
