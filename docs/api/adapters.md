# Adapters

Adapters are concrete implementations of the protocol interfaces. They wrap existing chains and tools from the codebase into the pluggable workflow system.

---

## Extractors

Claim extraction strategies implement the `ClaimExtractor` protocol.

### SimpleExtractor

::: truthfulness_evaluator.strategies.extractors.SimpleExtractor
    options:
      show_root_heading: true
      show_source: true

### TripletExtractor

::: truthfulness_evaluator.strategies.extractors.TripletExtractor
    options:
      show_root_heading: true
      show_source: true

---

## Gatherers

Evidence gathering strategies implement the `EvidenceGatherer` protocol.

### WebSearchGatherer

::: truthfulness_evaluator.strategies.gatherers.WebSearchGatherer
    options:
      show_root_heading: true
      show_source: true

### FilesystemGatherer

::: truthfulness_evaluator.strategies.gatherers.FilesystemGatherer
    options:
      show_root_heading: true
      show_source: true

### CompositeGatherer

::: truthfulness_evaluator.strategies.gatherers.CompositeGatherer
    options:
      show_root_heading: true
      show_source: true

---

## Verifiers

Claim verification strategies implement the `ClaimVerifier` protocol.

### SingleModelVerifier

::: truthfulness_evaluator.strategies.verifiers.SingleModelVerifier
    options:
      show_root_heading: true
      show_source: true

### ConsensusVerifier

::: truthfulness_evaluator.strategies.verifiers.ConsensusVerifier
    options:
      show_root_heading: true
      show_source: true

!!! note "ICE Consensus Status"
    The iterative critique/revise rounds for ICE (Iterative Consensus Ensemble) are currently stubbed. The implementation uses weighted voting but does not yet perform full debate-style refinement.

### InternalVerifier

::: truthfulness_evaluator.strategies.verifiers.InternalVerifier
    options:
      show_root_heading: true
      show_source: true

---

## Formatters

Report formatting strategies implement the `ReportFormatter` protocol.

### JsonFormatter

::: truthfulness_evaluator.strategies.formatters.JsonFormatter
    options:
      show_root_heading: true
      show_source: true

### MarkdownFormatter

::: truthfulness_evaluator.strategies.formatters.MarkdownFormatter
    options:
      show_root_heading: true
      show_source: true

### HtmlFormatter

::: truthfulness_evaluator.strategies.formatters.HtmlFormatter
    options:
      show_root_heading: true
      show_source: true
