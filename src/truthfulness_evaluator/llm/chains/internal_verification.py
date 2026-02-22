"""Internal verification - documentation alignment with codebase."""

import ast
import re
from pathlib import Path
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ...core.logging_config import get_logger
from ...models import Claim, Evidence, VerificationResult
from ..factory import create_chat_model

logger = get_logger()


# Structured output models
class ClaimClassification(BaseModel):
    """Classification of claim type."""

    claim_type: str = Field(
        description="Type: external_fact, api_signature, version_requirement, configuration, behavioral, or unknown"
    )
    confidence: float = Field(description="Confidence in classification (0.0-1.0)")
    reasoning: str = Field(description="Why this classification")


class InternalVerificationOutput(BaseModel):
    """Output for internal verification."""

    verdict: str = Field(description="SUPPORTS, REFUTES, or NOT_ENOUGH_INFO")
    confidence: float = Field(description="Confidence 0.0-1.0")
    reasoning: str = Field(description="Detailed explanation")
    actual_implementation: Optional[str] = Field(None, description="What was actually found")
    discrepancy: Optional[str] = Field(None, description="Specific discrepancy if any")


class ClaimClassifier:
    """Classify claims as external vs internal."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            base = create_chat_model(self.model, temperature=0)
            self._llm = base.with_structured_output(ClaimClassification)
        return self._llm

    async def classify(self, claim: Claim) -> ClaimClassification:
        """Determine if claim is about external facts or internal implementation."""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Classify this claim as one of:

1. external_fact - About history, science, general knowledge (verifiable online)
2. api_signature - About function/method signatures, parameters, return types
3. version_requirement - About version numbers, compatibility requirements
4. configuration - About config files, settings, defaults
5. behavioral - About what code does, behavior, side effects
6. unknown - Cannot determine

Examples:
- "Python was created in 1991" → external_fact
- "The process() function accepts a DataFrame" → api_signature
- "Requires Python 3.11 or higher" → version_requirement
- "Default port is 8080" → configuration
- "Returns processed data in 5 seconds" → behavioral
- "Multi-model truthfulness evaluation tool" → behavioral
- "Built on LangGraph and LangChain" → behavioral
- "See CLAUDE.md for project documentation" → configuration
- "Under active development" → external_fact
- "Supports web search and filesystem evidence" → behavioral
- "Uses Pydantic for data validation" → behavioral

Respond with classification and confidence.""",
                ),
                ("user", "Claim: {claim}"),
            ]
        )

        chain = prompt | self.llm
        return await chain.ainvoke({"claim": claim.text})


class InternalVerificationChain:
    """Verify documentation claims against actual codebase."""

    def __init__(self, root_path: str, model: str = "gpt-4o"):
        self.root_path = Path(root_path)
        self.model = model
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            base = create_chat_model(self.model, temperature=0)
            self._llm = base.with_structured_output(InternalVerificationOutput)
        return self._llm

    async def verify(self, claim: Claim, classification: ClaimClassification) -> VerificationResult:
        """Verify an internal claim against the codebase with confidence-based multi-model support."""

        # First attempt with primary model
        result = await self._verify_single_model(claim, classification)

        # If confidence is low or verdict is REFUTES, get second opinion
        if result.confidence < 0.7 or result.verdict == "REFUTES":
            logger.debug(
                f"Low confidence ({result.confidence:.0%}) or REFUTES — getting second opinion"
            )

            # Use different model for second opinion
            second_model = "gpt-4o" if "gpt-4o-mini" in self.model else "gpt-4o-mini"
            verifier2 = InternalVerificationChain(self.root_path, model=second_model)
            result2 = await verifier2._verify_single_model(claim, classification)

            # Combine results
            if result.verdict == result2.verdict:
                # Agreement - boost confidence
                result.confidence = max(result.confidence, result2.confidence) + 0.1
                result.confidence = min(result.confidence, 1.0)
                result.model_votes[self.model] = result.verdict
                result.model_votes[second_model] = result2.verdict
                result.explanation += (
                    f"\n\nSecond opinion ({second_model}): AGREES - {result2.explanation[:200]}"
                )
            else:
                # Disagreement - conservative NEI
                result.verdict = "NOT_ENOUGH_INFO"
                result.confidence = 0.5
                result.model_votes[self.model] = result.verdict
                result.model_votes[second_model] = result2.verdict
                result.explanation = f"Models disagree. Primary ({self.model}): {result.verdict}. Second ({second_model}): {result2.verdict}."

        return result

    async def _verify_single_model(
        self, claim: Claim, classification: ClaimClassification
    ) -> VerificationResult:
        """Verify with single model (internal method)."""

        if classification.claim_type == "api_signature":
            return await self._verify_api_claim(claim)
        elif classification.claim_type == "version_requirement":
            return await self._verify_version_claim(claim)
        elif classification.claim_type == "configuration":
            return await self._verify_config_claim(claim)
        elif classification.claim_type == "behavioral":
            return await self._verify_behavioral_claim(claim)
        else:
            # Best-effort: try behavioral verification for unknown claim types
            logger.info(
                f"Claim type '{classification.claim_type}' has no specific handler, "
                "falling back to behavioral verification"
            )
            return await self._verify_behavioral_claim(claim)

    async def _verify_api_claim(self, claim: Claim) -> VerificationResult:
        """Verify API signature claim against actual code."""

        # Extract function name from claim
        function_name = self._extract_function_name(claim.text)
        if not function_name:
            return self._nei_result(claim, "Could not extract function name from claim")

        # Search for function in codebase
        implementation = await self._find_function_implementation(function_name)

        if not implementation:
            return self._nei_result(claim, f"Function '{function_name}' not found in codebase")

        # Use LLM to compare claim against implementation
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Compare the documentation claim against the actual implementation.

Determine if the claim accurately describes the implementation.

Respond with:
- verdict: SUPPORTS (accurate), REFUTES (inaccurate), or NOT_ENOUGH_INFO
- confidence: 0.0-1.0
- reasoning: Detailed comparison
- actual_implementation: Brief description of what was found
- discrepancy: Specific differences if REFUTES""",
                ),
                (
                    "user",
                    """Documentation claim: {claim}

Actual implementation:
{implementation}

Compare and verify.""",
                ),
            ]
        )

        chain = prompt | self.llm
        result: InternalVerificationOutput = await chain.ainvoke(
            {"claim": claim.text, "implementation": implementation}
        )

        evidence = Evidence(
            source=str(self.root_path / f"{function_name}_implementation"),
            source_type="filesystem",
            content=implementation[:1000],
            relevance_score=1.0 if result.verdict == "SUPPORTS" else 0.5,
        )

        return VerificationResult(
            claim_id=claim.id,
            verdict=result.verdict,
            confidence=result.confidence,
            evidence=[evidence],
            explanation=result.reasoning
            + (
                f"\n\nActual: {result.actual_implementation}"
                if result.actual_implementation
                else ""
            ),
            model_votes={self.model: result.verdict},
        )

    async def _verify_version_claim(self, claim: Claim) -> VerificationResult:
        """Verify version requirement claim against pyproject.toml, setup.py, etc."""

        # Check common version files - prioritize based on claim content
        claim_lower = claim.text.lower()

        # Determine which files to check based on claim content
        version_files = []

        if "python" in claim_lower:
            version_files = ["pyproject.toml", "setup.py", "setup.cfg", ".python-version"]
        elif "node" in claim_lower or "npm" in claim_lower:
            version_files = ["package.json", ".nvmrc"]
        elif "rust" in claim_lower or "cargo" in claim_lower:
            version_files = ["Cargo.toml", "rust-toolchain"]
        else:
            # Generic fallback
            version_files = ["pyproject.toml", "setup.py", "package.json", "Cargo.toml"]

        found_versions = []

        for filename in version_files:
            filepath = self.root_path / filename
            if filepath.exists():
                try:
                    content = filepath.read_text()
                    version_info = self._extract_version_info(content, filename)
                    if version_info:
                        found_versions.append((filename, version_info))
                except Exception:
                    continue

        if not found_versions:
            return self._nei_result(claim, "No version files found in codebase")

        # Compare claim against found versions
        versions_text = "\n".join([f"{f}: {v}" for f, v in found_versions])

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Compare the claimed version requirement against actual configuration files.",
                ),
                (
                    "user",
                    """Claim: {claim}

Found in config files:
{versions}

Does the claim match?""",
                ),
            ]
        )

        chain = prompt | self.llm
        result: InternalVerificationOutput = await chain.ainvoke(
            {"claim": claim.text, "versions": versions_text}
        )

        evidence = [
            Evidence(
                source=str(self.root_path / f),
                source_type="filesystem",
                content=v[:500],
                relevance_score=1.0,
            )
            for f, v in found_versions
        ]

        return VerificationResult(
            claim_id=claim.id,
            verdict=result.verdict,
            confidence=result.confidence,
            evidence=evidence,
            explanation=result.reasoning,
            model_votes={self.model: result.verdict},
        )

    async def _verify_config_claim(self, claim: Claim) -> VerificationResult:
        """Verify configuration claim against config files."""

        # Smart config file selection based on claim content
        claim_lower = claim.text.lower()

        # Prioritize specific config files
        priority_files = []

        if "default" in claim_lower and "model" in claim_lower:
            # Look for config.py or settings files
            priority_files = [
                "src/truthfulness_evaluator/config.py",
                "src/config.py",
                "config.py",
                "settings.py",
                "pyproject.toml",
            ]
        elif "threshold" in claim_lower or "confidence" in claim_lower:
            priority_files = [
                "src/truthfulness_evaluator/config.py",
                "config.py",
                "settings.yaml",
                "pyproject.toml",
            ]
        else:
            # Generic config search
            priority_files = [
                "src/**/config.py",
                "src/**/settings.py",
                "config.yaml",
                "config.json",
            ]

        config_files = []
        for pattern in priority_files:
            if "**" in pattern:
                config_files.extend(self.root_path.glob(pattern))
            else:
                f = self.root_path / pattern
                if f.exists():
                    config_files.append(f)

        # Also check generic patterns if no priority files found
        if not config_files:
            config_patterns = ["*.toml", "*.yaml", "*.yml", "*.json"]
            for pattern in config_patterns:
                config_files.extend(self.root_path.glob(pattern))

        if not config_files:
            return self._nei_result(claim, "No config files found")

        # Read config files (limit to first few)
        configs = []
        for cfg_file in config_files[:3]:
            try:
                content = cfg_file.read_text()
                configs.append(f"{cfg_file.name}:\n{content[:1000]}")
            except (OSError, UnicodeDecodeError):
                pass

        configs_text = "\n\n".join(configs)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "Verify if the configuration claim matches the actual config files."),
                (
                    "user",
                    """Claim: {claim}

Config files:
{configs}

Does the claim match the configuration?""",
                ),
            ]
        )

        chain = prompt | self.llm
        result: InternalVerificationOutput = await chain.ainvoke(
            {"claim": claim.text, "configs": configs_text}
        )

        evidence = [
            Evidence(
                source=str(f),
                source_type="filesystem",
                content=f.read_text()[:500] if f.exists() else "",
                relevance_score=0.9,
            )
            for f in config_files[:3]
        ]

        return VerificationResult(
            claim_id=claim.id,
            verdict=result.verdict,
            confidence=result.confidence,
            evidence=evidence,
            explanation=result.reasoning,
            model_votes={self.model: result.verdict},
        )

    async def _verify_behavioral_claim(self, claim: Claim) -> VerificationResult:
        """Verify behavioral claim by searching for implementation keywords."""

        claim_lower = claim.text.lower()

        # Define keyword patterns for different behavioral claims
        keyword_patterns = {
            "multi-model": ["consensus", "multi.*model", "vote", "models"],
            "consensus": ["consensus", "voting", "agreement"],
            "react agent": ["react", "agent", "filesystem", "browse"],
            "filesystem": ["filesystem", "file.*search", "read_file", "list_files"],
            "pydantic": ["pydantic", "basemodel", "structured_output"],
            "web search": ["duckduckgo", "web.*search", "search_tool"],
            "langgraph": ["langgraph", "stategraph", "checkpoint"],
            "streaming": ["stream", "astream", "streaming"],
            "cli": ["cli", "typer", "click", "command"],
        }

        # Find matching patterns
        matched_patterns = []
        for _concept, patterns in keyword_patterns.items():
            if any(p.replace(".*", "").replace("_", " ") in claim_lower for p in patterns):
                matched_patterns.extend(patterns)

        # If no specific patterns, extract key nouns
        if not matched_patterns:
            words = claim_lower.split()
            keywords = [
                w for w in words if len(w) > 4 and w not in ["the", "tool", "uses", "with", "from"]
            ]
            matched_patterns = keywords[:3]

        # Search codebase for evidence
        found_files = []

        for py_file in self.root_path.rglob("*.py"):
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                content = py_file.read_text().lower()

                for pattern in matched_patterns:
                    clean_pattern = pattern.replace(".*", "").lower()
                    if clean_pattern in content:
                        found_files.append(py_file)
                        break

            except Exception:
                continue

        found_files = list(set(found_files))[:5]

        if found_files:
            evidence = [
                Evidence(
                    source=str(f.relative_to(self.root_path)),
                    source_type="filesystem",
                    content=f"Contains implementation of: {', '.join(matched_patterns[:3])}",
                    relevance_score=0.8,
                    supports_claim=True,
                )
                for f in found_files
            ]

            return VerificationResult(
                claim_id=claim.id,
                verdict="SUPPORTS",
                confidence=0.7,
                evidence=evidence,
                explanation=f"Found implementation evidence in {len(found_files)} files: {', '.join(str(f.name) for f in found_files)}",
                model_votes={self.model: "SUPPORTS"},
            )

        return self._nei_result(
            claim, f"Could not find implementation evidence for keywords: {matched_patterns[:3]}"
        )

    def _extract_function_name(self, claim_text: str) -> Optional[str]:
        """Extract function/method name from claim text."""
        # Look for patterns like "The process() function", "process() accepts", etc.
        patterns = [
            r"The\s+(\w+)\s*\(\)\s+function",
            r"(\w+)\s*\(\)\s+(?:accepts|returns|takes)",
            r"function\s+(\w+)\s*\(",
            r"method\s+(\w+)\s*\(",
        ]

        for pattern in patterns:
            match = re.search(pattern, claim_text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    async def _find_function_implementation(self, function_name: str) -> Optional[str]:
        """Find and extract function implementation from codebase."""

        matches = []

        # Search Python files (prioritize src/ directory)
        search_paths = [self.root_path / "src", self.root_path]

        for search_path in search_paths:
            if not search_path.exists():
                continue

            for py_file in search_path.rglob("*.py"):
                if (
                    ".venv" in str(py_file)
                    or "__pycache__" in str(py_file)
                    or ".git" in str(py_file)
                ):
                    continue

                try:
                    content = py_file.read_text()

                    # Try AST parsing first (most reliable)
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if (
                                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                                and node.name == function_name
                            ):
                                # Extract function source
                                lines = content.split("\n")
                                start_line = node.lineno - 1
                                end_line = (
                                    node.end_lineno
                                    if hasattr(node, "end_lineno")
                                    else start_line + 20
                                )
                                func_source = "\n".join(lines[start_line:end_line])

                                # Also get docstring if available
                                docstring = ast.get_docstring(node)

                                result = (
                                    f"File: {py_file.relative_to(self.root_path)}\n\n{func_source}"
                                )
                                if docstring:
                                    result += f"\n\nDocstring: {docstring[:500]}"

                                matches.append((py_file, result, len(func_source)))
                    except SyntaxError:
                        pass

                    # Fallback: regex search for function definition
                    if not matches:
                        pattern = rf"(?:async\s+)?def\s+{re.escape(function_name)}\s*\([^)]*\)(?:\s*->\s*[^:]+)?:"
                        match = re.search(pattern, content)
                        if match:
                            start = match.start()
                            # Extract ~30 lines after match
                            lines = content[start:].split("\n")[:30]
                            snippet = "\n".join(lines)
                            matches.append(
                                (
                                    py_file,
                                    f"File: {py_file.relative_to(self.root_path)}\n\n{snippet}",
                                    len(snippet),
                                )
                            )

                except Exception:
                    continue

        # Return the best match (longest implementation = most detail)
        if matches:
            matches.sort(key=lambda x: x[2], reverse=True)
            return matches[0][1]

        return None

    def _extract_version_info(self, content: str, filename: str) -> Optional[str]:
        """Extract version info from config file content."""
        if filename == "pyproject.toml":
            # Look for requires-python
            match = re.search(r'requires-python\s*=\s*"([^"]+)"', content)
            if match:
                return f'requires-python = "{match.group(1)}"'
            # Look for version
            match = re.search(r'version\s*=\s*"([^"]+)"', content)
            if match:
                return f'version = "{match.group(1)}"'

        elif filename == "setup.py":
            match = re.search(r'python_requires\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return f"python_requires='{match.group(1)}'"

        elif filename == "package.json":
            match = re.search(r'"version"\s*:\s*"([^"]+)"', content)
            if match:
                return f"version: {match.group(1)}"

        return None

    def _nei_result(self, claim: Claim, explanation: str) -> VerificationResult:
        """Create a NOT_ENOUGH_INFO result."""
        return VerificationResult(
            claim_id=claim.id,
            verdict="NOT_ENOUGH_INFO",
            confidence=0.0,
            evidence=[],
            explanation=explanation,
            model_votes={self.model: "NOT_ENOUGH_INFO"},
        )
