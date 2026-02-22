# Graph

## create_truthfulness_graph

```python
from truthfulness_evaluator.llm.workflows.graph import create_truthfulness_graph

graph = create_truthfulness_graph()
```

Returns a compiled LangGraph with checkpointing.

## State

```python
from truthfulness_evaluator.llm.workflows.state import WorkflowState

class WorkflowState(TypedDict):
    document: str
    document_path: str
    root_path: str | None
    claims: list[Claim]
    current_claim_index: int
    verifications: list[VerificationResult]
    evidence_cache: dict[str, list[Evidence]]
    config: dict
    final_report: TruthfulnessReport | None
```

## Nodes

| Node | Function | Description |
|------|----------|-------------|
| `extract_claims` | `extract_claims_node` | Extract claims from document |
| `search_evidence` | `search_evidence_node` | Search web + filesystem |
| `verify_claim` | `verify_claim_node` | Multi-model verification |
| `generate_report` | `generate_report_node` | Create final report |

## Usage

### Basic

```python
result = await graph.ainvoke({
    "document": "Python was created in 1991...",
    "document_path": "README.md",
    "root_path": None,
    "claims": [],
    "current_claim_index": 0,
    "verifications": [],
    "evidence_cache": {},
    "config": config.model_dump(),
    "final_report": None
})

report = result["final_report"]
```

Note: `config` above refers to an `EvaluatorConfig` instance from `truthfulness_evaluator.core.config`.

### With Checkpointing

```python
config = {"configurable": {"thread_id": "eval_1"}}

# Start
result = await graph.ainvoke(input_state, config)

# Resume (after interruption)
result = await graph.ainvoke(None, config)
```

### Streaming

```python
async for event in graph.astream(
    input_state,
    config,
    stream_mode="updates"
):
    if "extract_claims" in event:
        print(f"Extracted {len(event['extract_claims']['claims'])} claims")
    elif "verify_claim" in event:
        print("Verified claim")
```

### Human-in-the-Loop

```python
from langgraph.types import interrupt, Command

# In verify_claim_node:
human_input = interrupt({
    "claim": claim.text,
    "proposed_verdict": verification.verdict,
    "question": "Approve?"
})

# Resume:
result = await graph.ainvoke(
    Command(resume={"response": "approve"}),
    config
)
```

## Custom Graph

Build your own workflow:

```python
from langgraph.graph import StateGraph, START, END
from truthfulness_evaluator.llm.workflows.state import WorkflowState

builder = StateGraph(WorkflowState)

# Add nodes
builder.add_node("extract", extract_claims_node)
builder.add_node("verify", verify_claim_node)

# Add edges
builder.add_edge(START, "extract")
builder.add_edge("extract", "verify")
builder.add_edge("verify", END)

# Compile with checkpointing
from langgraph.checkpoint.memory import MemorySaver
graph = builder.compile(checkpointer=MemorySaver())
```

## Time Travel

```python
# Get state history
history = graph.get_state_history(config)
for state in history:
    print(f"Step {state.step}: {state.values.keys()}")

# Branch from specific point
past_state = history[3]  # Step 3
new_config = graph.get_state(past_state.config)
```

## API Reference

### Graph Creation

::: truthfulness_evaluator.llm.workflows.graph.create_truthfulness_graph
    options:
      show_root_heading: true
      show_source: true

### State

::: truthfulness_evaluator.llm.workflows.state.WorkflowState
    options:
      show_root_heading: true
      show_source: true

### Configuration

::: truthfulness_evaluator.core.config.EvaluatorConfig
    options:
      show_root_heading: true
      show_source: true
