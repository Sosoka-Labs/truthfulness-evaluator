# Multi-Model Consensus

## Why Use Multiple Models?

Single models can hallucinate. Multiple models voting reduces false positives.

| Setup | Accuracy | Speed | Cost |
|-------|----------|-------|------|
| Single model | Good | Fast | Low |
| 2 models | Better | Medium | Medium |
| 3+ models | Best | Slow | Higher |

!!! example "When to Use Multi-Model"
    Use single model verification for quick checks and draft reviews where perfect accuracy isn't critical. Use 2-model consensus for production documentation that users depend on. Use 3+ models with high confidence thresholds for legal, medical, or safety-critical documentation where errors have serious consequences.

!!! tip "Model Selection Strategy"
    Pair models from different providers (GPT-4o + Claude) rather than different sizes from the same family (GPT-4o + GPT-4o-mini). Cross-provider diversity catches more hallucinations since models have different training data and architectures.

## Basic Consensus

```bash
truth-eval README.md \
  --model gpt-4o \
  --model gpt-4o-mini
```

## High-Confidence Setup

```bash
truth-eval critical-doc.md \
  --model gpt-4o \
  --model claude-sonnet-4-5 \
  --model gpt-4o-mini \
  --confidence 0.8
```

## How Consensus Works

Consensus is **agreement-based**, not an average of self-reported confidence. Each model
in the panel returns its own verdict; `ConsensusChain` tallies verdicts using per-model
weights (equal by default), then:

- Commits the leading verdict **only if** it isn't tied for the lead **and** its weighted
  agreement fraction meets `confidence_threshold`.
- Otherwise abstains to `NOT_ENOUGH_INFO`.

The reported `confidence` on the result *is* that weighted agreement fraction — a
consistency signal — not a mean of the models' own confidence scores, which research on
LLM calibration found to be unreliable (see `llm_memory/research-multimodel-voting.md`
in the repository root for the full rationale).

### Unanimous Agreement

```
gpt-4o: SUPPORTS
gpt-4o-mini: SUPPORTS
→ Final: SUPPORTS (confidence 1.0 — 100% weighted agreement)
```

### Tie

```
gpt-4o: SUPPORTS
gpt-4o-mini: REFUTES
→ Final: NOT_ENOUGH_INFO (tie for the lead — no verdict has a majority)
```

### Majority That Still Misses the Threshold

With 3 equal-weight models, a 2-out-of-3 majority is only 0.67 weighted agreement:

```
gpt-4o: SUPPORTS
claude-sonnet-4-5: SUPPORTS
gpt-4o-mini: NOT_ENOUGH_INFO
→ confidence_threshold=0.7 → Final: NOT_ENOUGH_INFO (0.67 < 0.7 threshold, abstains)
→ confidence_threshold=0.6 → Final: SUPPORTS (confidence 0.67, majority accepted)
```

Lower `confidence_threshold` to accept simple majorities; raise it toward unanimity for
higher-precision, lower-yield verdicts.

## Python API

```python
from truthfulness_evaluator.llm.chains.consensus import ConsensusChain

consensus = ConsensusChain(
    model_names=["gpt-4o", "gpt-4o-mini", "claude-sonnet-4-5"],
    weights={
        "gpt-4o": 0.4,
        "claude-sonnet-4-5": 0.4,
        "gpt-4o-mini": 0.2
    },
    confidence_threshold=0.7
)

result = await consensus.verify(claim, evidence)
print(result.model_votes)
# {'gpt-4o': 'SUPPORTS', 'gpt-4o-mini': 'SUPPORTS', 'claude-sonnet-4-5': 'SUPPORTS'}
```

### Real Consensus Output Examples

`ConsensusChain.verify()` returns a `VerificationResult`. Its `model_votes` field is a
flat mapping of model name to that model's verdict string — there is no per-model
confidence or reasoning breakdown in `model_votes` itself; the per-model self-reported
confidence is only summarized in the human-readable `explanation` text.

#### Example 1: Unanimous Agreement

```json
{
  "claim_id": "c-104",
  "verdict": "SUPPORTS",
  "confidence": 1.0,
  "model_votes": {
    "gpt-4o": "SUPPORTS",
    "gpt-4o-mini": "SUPPORTS"
  },
  "explanation": "Consensus: SUPPORTS (100% weighted agreement)\nModel votes:\ngpt-4o: SUPPORTS (self-reported 95%)\ngpt-4o-mini: SUPPORTS (self-reported 91%)"
}
```

#### Example 2: Disagreement Leading to NOT_ENOUGH_INFO

```json
{
  "claim_id": "c-207",
  "verdict": "NOT_ENOUGH_INFO",
  "confidence": 0.5,
  "model_votes": {
    "gpt-4o": "NOT_ENOUGH_INFO",
    "gpt-4o-mini": "REFUTES"
  },
  "explanation": "Consensus: NOT_ENOUGH_INFO (50% weighted agreement)\nModel votes:\ngpt-4o: NOT_ENOUGH_INFO (self-reported 50%)\ngpt-4o-mini: REFUTES (self-reported 70%)\n(Abstained: tie.)"
}
```

Note `confidence` here is the weighted agreement fraction (a tie between two verdicts,
each at 50% of the weight), not either model's self-reported confidence.

## When to Use

| Scenario | Recommendation |
|----------|----------------|
| Quick check | Single model (gpt-4o) |
| Documentation | 2 models |
| Legal/medical | 3+ models + high agreement threshold |
| Research paper | 3+ diverse models + high agreement threshold |

## Cost Optimization

```python
# Cheap extraction, expensive verification
config = EvaluatorConfig(
    claim_extraction_model="gpt-4o-mini",  # $0.15/M tokens
    verification_models=["gpt-4o"],   # $2.50/M tokens
)
```

## Interpreting Disagreements

```
Claim: "Feature X was added in v2.0"

gpt-4o: SUPPORTS
gpt-4o-mini: REFUTES

→ Check:
- Different evidence sources?
- Ambiguous wording?
- Outdated information?
```

Disagreement = need for human review.

!!! warning "Common Disagreement Causes"
    Models often disagree when evidence is ambiguous, sources contradict each other, or claims use imprecise language. For example, "supports Python 3.11" could mean "requires 3.11+" or "works with 3.11 among other versions". Rewrite ambiguous claims more precisely to reduce disagreement.

## Advanced Consensus Strategies

### Agreement Thresholds

`confidence_threshold` sets the minimum weighted agreement required to commit a verdict:

```python
consensus = ConsensusChain(
    model_names=["gpt-4o", "gpt-4o-mini"],
    confidence_threshold=0.85  # Require 85% weighted agreement to commit a verdict
)
```

Results that don't clear the threshold abstain to `NOT_ENOUGH_INFO`, which is a signal to
trigger human review or gather additional evidence.

### Weighted Voting

Assign different weights to models based on their reliability:

```python
consensus = ConsensusChain(
    model_names=["gpt-4o", "claude-sonnet-4-5", "gpt-4o-mini"],
    weights={
        "gpt-4o": 0.4,          # 40% weight - strong general reasoning
        "claude-sonnet-4-5": 0.4,  # 40% weight - excellent code understanding
        "gpt-4o-mini": 0.2      # 20% weight - faster but less accurate
    }
)
```

The final confidence score is the weighted **agreement** fraction for the leading
verdict — the fraction of total weight that voted for it — not an average of the models'
individual confidence scores.

### Ties Always Abstain

`ConsensusChain` has one tie-breaking rule: if two or more verdicts are tied for the most
weight, the result is always `NOT_ENOUGH_INFO`. There is no configurable tie-break
strategy — ties are treated the same as insufficient agreement.

```
gpt-4o: SUPPORTS
gpt-4o-mini: REFUTES
→ Final: NOT_ENOUGH_INFO (tie, regardless of confidence_threshold)
```
