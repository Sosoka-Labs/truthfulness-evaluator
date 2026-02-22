# Protocols

The protocol layer defines the core abstractions for the truthfulness evaluation pipeline. Each protocol represents a distinct responsibility in the workflow:

- **ClaimExtractor**: Extracts factual claims from input documents
- **EvidenceGatherer**: Gathers supporting or refuting evidence for claims
- **ClaimVerifier**: Verifies claims against collected evidence
- **ReportFormatter**: Formats verification results into human-readable reports

These protocols enable pluggable strategies, allowing you to mix and match different implementations for each stage of the pipeline.

---

## ClaimExtractor

::: truthfulness_evaluator.protocols.ClaimExtractor
    options:
      show_root_heading: true
      show_source: true

**Usage Note**: Concrete implementations include `SimpleExtractor` (general-purpose) and `TripletExtractor` (subject-predicate-object triples).

---

## EvidenceGatherer

::: truthfulness_evaluator.protocols.EvidenceGatherer
    options:
      show_root_heading: true
      show_source: true

**Usage Note**: Implementations range from `WebSearchGatherer` (web-based evidence) to `FilesystemGatherer` (local file evidence) to `CompositeGatherer` (combines multiple gatherers).

---

## ClaimVerifier

::: truthfulness_evaluator.protocols.ClaimVerifier
    options:
      show_root_heading: true
      show_source: true

**Usage Note**: Choose between `SingleModelVerifier` (fast, single LLM), `ConsensusVerifier` (multi-model voting), or `InternalVerifier` (code-documentation alignment).

---

## ReportFormatter

::: truthfulness_evaluator.protocols.ReportFormatter
    options:
      show_root_heading: true
      show_source: true

**Usage Note**: Built-in formatters support JSON, Markdown, and HTML output. Implement this protocol to add custom report formats.
