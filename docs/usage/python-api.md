# Python API

## Basic Usage

```python
import asyncio
from truthfulness_evaluator import create_truthfulness_graph
from truthfulness_evaluator.config import EvaluatorConfig

async def evaluate():
    # Configure
    config = EvaluatorConfig(
        verification_models=["gpt-4o"],
        enable_web_search=True
    )
    
    # Create graph
    graph = create_truthfulness_graph()
    
    # Run evaluation
    result = await graph.ainvoke({
        "document": "Python was created in 1991.",
        "document_path": "test.md",
        "root_path": None,
        "claims": [],
        "current_claim_index": 0,
        "verifications": [],
        "evidence_cache": {},
        "config": config.model_dump(),
        "final_report": None
    })
    
    return result["final_report"]

report = asyncio.run(evaluate())
```

## Components

### Claim Extraction

```python
from truthfulness_evaluator.chains.extraction import SimpleClaimExtractionChain

extractor = SimpleClaimExtractionChain(model="gpt-4o-mini")
claims = await extractor.extract(
    document="Python was created in 1991.",
    source_path="test.md"
)

for claim in claims:
    print(f"{claim.id}: {claim.text}")
```

### Verification

```python
from truthfulness_evaluator.chains.verification import VerificationChain
from truthfulness_evaluator.models import Claim, Evidence

verifier = VerificationChain(model_name="gpt-4o")

claim = Claim(id="c1", text="Python was created in 1991", source_document="test.md")
evidence = [Evidence(
    source="python.org",
    source_type="web",
    content="Python was created by Guido van Rossum...",
    relevance_score=0.9
)]

result = await verifier.verify(claim, evidence)
print(f"{result.verdict} ({result.confidence:.0%})")
```

### Consensus

```python
from truthfulness_evaluator.chains.consensus import ConsensusChain

consensus = ConsensusChain(
    model_names=["gpt-4o", "gpt-4o-mini"],
    confidence_threshold=0.7
)

result = await consensus.verify(claim, evidence)
print(result.model_votes)  # {'gpt-4o': 'SUPPORTS', 'gpt-4o-mini': 'SUPPORTS'}
```

### Evidence Processing

```python
from truthfulness_evaluator.chains.evidence import EvidenceProcessor

processor = EvidenceProcessor(model="gpt-4o-mini")
evidence, summary = await processor.analyze_evidence(claim, evidence_list)

print(summary)
for e in evidence:
    print(f"{e.source}: relevance={e.relevance_score:.0%}")
```

## Streaming

```python
async for event in graph.astream(
    input_state,
    config={"configurable": {"thread_id": "eval_1"}},
    stream_mode="updates"
):
    if "extract_claims" in event:
        print(f"Extracted {len(event['extract_claims']['claims'])} claims")
    elif "verify_claim" in event:
        print("Verified claim")
```

## Checkpointing

Resume interrupted evaluations:

```python
config = {"configurable": {"thread_id": "eval_1"}}

# Start
result = await graph.ainvoke(input_state, config)

# Resume after interruption
result = await graph.ainvoke(None, config)
```

## Human-in-the-Loop

```python
from langgraph.types import Command

# Interrupt for human review
human_input = interrupt({
    "claim": claim.text,
    "proposed_verdict": verification.verdict,
    "question": "Approve?"
})

# Resume with human input
result = await graph.ainvoke(
    Command(resume={"response": "approve"}),
    config
)
```

## Custom Workflows

Build your own graph:

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(TruthfulnessState)
builder.add_node("extract", extract_claims_node)
builder.add_node("verify", verify_claim_node)
builder.add_edge(START, "extract")
builder.add_edge("extract", "verify")
builder.add_edge("verify", END)

graph = builder.compile()
```
