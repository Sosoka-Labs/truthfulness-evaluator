# Design Philosophy

## Two Types of Truth

The Truthfulness Evaluator distinguishes between two fundamentally different types of claims that require different verification approaches.

### 1. External Facts (World Truth)

Claims about the external world that can be verified against authoritative sources.

**Examples:**

- "Python was created in 1991" → Verify against python.org, Wikipedia
- "OpenAI was founded in 2015" → Verify against OpenAI's about page
- "The speed of light is 299,792,458 m/s" → Verify against physics references

**Verification Method:** Web search, knowledge bases, authoritative sources

### 2. Code-Documentation Alignment (Implementation Truth)

Claims about what the code does, its API, behavior, or requirements.

**Examples:**

- "The `process()` function accepts a DataFrame" → Verify against actual function signature
- "Requires Python 3.11 or higher" → Verify against pyproject.toml
- "Returns a dictionary with keys 'id' and 'name'" → Verify against return statement

**Verification Method:** Parse code, extract signatures, compare semantics

## Why Both Matter

Different scenarios require different verification strategies:

| Scenario | External Facts | Code Alignment |
|----------|---------------|----------------|
| README claims about Python history | ✅ Critical | ❌ N/A |
| API documentation accuracy | ❌ N/A | ✅ Critical |
| Performance benchmarks | ✅ Verify sources | ✅ Verify implementation |
| Version requirements | ❌ N/A | ✅ Critical |

!!! note "Current Implementation"
    We have **partial** code alignment via filesystem tools:

    - `FilesystemEvidenceAgent` - Can browse files
    - `grep_files` - Can search for patterns
    - `read_file` - Can read source

    However, these tools are **generic** and not code-aware. Full semantic understanding of code structure is planned for future releases.

## Architecture for Full Code-Documentation Alignment

### 1. Code-Aware Claim Extraction

Claims should be classified by type to route them to appropriate verification strategies:

```python
class ClaimType(Enum):
    EXTERNAL_FACT = "external_fact"      # "Python created 1991"
    API_SIGNATURE = "api_signature"      # "process() accepts DataFrame"
    VERSION_REQUIREMENT = "version_req"  # "Requires Python 3.11+"
    BEHAVIORAL = "behavioral"            # "Returns processed data"
    CONFIGURATION = "config"             # "Default port is 8080"
```

### 2. Code Parsing Tools

Specialized tools for extracting structured information from code:

```python
@tool
def parse_function_signature(file_path: str, function_name: str) -> dict:
    """Extract function signature from Python file using AST."""

@tool
def extract_class_interface(file_path: str, class_name: str) -> dict:
    """Extract public methods and attributes from class."""

@tool
def read_config_value(file_path: str, key: str) -> str:
    """Extract value from config file (pyproject.toml, package.json, etc)."""
```

### 3. Semantic Comparison

A dedicated chain for verifying code-documentation alignment:

```python
class CodeDocumentationAlignmentChain:
    """Verify that docs accurately describe code."""

    async def verify_api_claim(self, claim: str, codebase: Path) -> VerificationResult:
        # 1. Parse claim to extract claimed signature
        # 2. Find actual implementation
        # 3. Compare claimed vs actual
        # 4. Report discrepancies
```

### 4. Router Pattern

Route claims to the appropriate verification strategy:

```python
async def route_claim(claim: Claim) -> VerificationStrategy:
    """Determine how to verify this claim."""

    if is_external_fact(claim):
        return ExternalFactChecker()  # Web search

    elif is_code_claim(claim):
        return CodeAlignmentChecker()  # Parse codebase

    elif is_config_claim(claim):
        return ConfigAlignmentChecker()  # Read config files

    else:
        return GenericChecker()  # Both/unsure
```

## Implementation Roadmap

### Phase 1: Enhanced Code Awareness (High Value)

- Add AST parsing for Python
- Extract function/class signatures
- Compare against documentation

### Phase 2: Multi-Language Support

- JavaScript/TypeScript parsing
- Rust, Go signatures
- Language-agnostic interface

### Phase 3: Behavioral Verification

- Type compatibility checking
- Return value verification
- Side-effect detection

## Example: Enhanced Code Verification

Consider this README claim:

```markdown
# README.md

## API

The `process_data()` function accepts:
- `data`: DataFrame or dict
- `batch_size`: int (default 100)
- Returns: Processed DataFrame
```

**Current Tool Behavior:**

- Searches web for "process_data function" ❌ Wrong approach
- Maybe finds source file ⚠️ Generic text search

**Enhanced Tool Behavior:**

1. Classifies claim as `API_SIGNATURE`
2. Parses `src/core.py` to find `process_data`
3. Extracts actual signature:
   ```python
   def process_data(data: Union[pd.DataFrame, dict],
                    batch_size: int = 100) -> pd.DataFrame:
   ```
4. Compares: claimed vs actual ✅ Match!
5. Reports: "API documentation accurate"

!!! success "Value Proposition"
    **Pros:**

    - Higher value for developers (most docs are about code, not history)
    - Differentiated capability
    - Catches doc drift automatically

    **Cons:**

    - Language-specific complexity
    - AST parsing is brittle
    - More maintenance burden

## Mode Selection

The tool supports multiple verification modes:

```bash
# External facts only (current default)
truth-eval README.md

# Code alignment only
truth-eval README.md --mode internal

# Both
truth-eval README.md --mode both
```

This preserves the current external fact-checking capability while enabling high-value code alignment verification when needed.

!!! tip "Choosing a Mode"
    - Use **external** mode for general documentation, historical claims, and conceptual explanations
    - Use **internal** mode for API docs, configuration claims, and version requirements
    - Use **both** mode for comprehensive verification of technical documentation that mixes conceptual and implementation details
