"""Tests for InternalVerificationChain.

Focuses on the deterministic surface: the regex/parse helpers, the keyword
behavioral search (against a tmp_path tree), and claim-type dispatch. The
LLM-backed comparison steps are out of scope here (covered by the e2e suite).
"""

from pathlib import Path
from unittest.mock import AsyncMock

from truthfulness_evaluator.llm.chains.internal_verification import (
    ClaimClassification,
    InternalVerificationChain,
)
from truthfulness_evaluator.models import Claim, VerificationResult


def _claim(text: str = "Some claim.") -> Claim:
    return Claim(id="c1", text=text, source_document="doc.txt")


def _chain(root: str = ".") -> InternalVerificationChain:
    return InternalVerificationChain(root_path=root, model="gpt-4o")


class TestExtractFunctionName:
    def test_the_x_function_pattern(self):
        assert _chain()._extract_function_name("The process() function reads data") == "process"

    def test_accepts_returns_takes_pattern(self):
        assert _chain()._extract_function_name("load() accepts a path") == "load"

    def test_function_keyword_pattern(self):
        assert _chain()._extract_function_name("Call the function parse(x) here") == "parse"

    def test_method_keyword_pattern(self):
        assert _chain()._extract_function_name("The method run() is invoked") == "run"

    def test_no_match_returns_none(self):
        assert _chain()._extract_function_name("A plain sentence with no calls.") is None


class TestExtractVersionInfo:
    def test_pyproject_requires_python(self):
        content = 'requires-python = ">=3.11"'
        assert (
            _chain()._extract_version_info(content, "pyproject.toml")
            == 'requires-python = ">=3.11"'
        )

    def test_pyproject_version_fallback(self):
        content = 'version = "1.2.3"'
        assert _chain()._extract_version_info(content, "pyproject.toml") == 'version = "1.2.3"'

    def test_setup_py_python_requires(self):
        content = "python_requires='>=3.8'"
        assert _chain()._extract_version_info(content, "setup.py") == "python_requires='>=3.8'"

    def test_package_json_version(self):
        content = '"version": "2.0.0"'
        assert _chain()._extract_version_info(content, "package.json") == "version: 2.0.0"

    def test_unknown_file_returns_none(self):
        assert _chain()._extract_version_info("anything", "Cargo.toml") is None


class TestNeiResult:
    def test_builds_not_enough_info(self):
        result = _chain()._nei_result(_claim(), "no evidence")
        assert isinstance(result, VerificationResult)
        assert result.verdict == "NOT_ENOUGH_INFO"
        assert result.confidence == 0.0
        assert result.evidence == []
        assert result.explanation == "no evidence"
        assert result.model_votes == {"gpt-4o": "NOT_ENOUGH_INFO"}


class TestVerifyBehavioralClaim:
    async def test_finds_keyword_evidence(self, tmp_path: Path):
        (tmp_path / "core.py").write_text("from pydantic import BaseModel\n")
        chain = _chain(str(tmp_path))
        result = await chain._verify_behavioral_claim(_claim("Uses Pydantic for validation"))
        assert result.verdict == "SUPPORTS"
        assert result.confidence == 0.7
        assert result.evidence

    async def test_no_evidence_yields_nei(self, tmp_path: Path):
        (tmp_path / "empty.py").write_text("x = 1\n")
        chain = _chain(str(tmp_path))
        result = await chain._verify_behavioral_claim(
            _claim("Implements quantum teleportation subsystems")
        )
        assert result.verdict == "NOT_ENOUGH_INFO"


class TestVerifySingleModelDispatch:
    async def test_routes_by_claim_type(self):
        chain = _chain()
        chain._verify_api_claim = AsyncMock(return_value="api")
        chain._verify_version_claim = AsyncMock(return_value="version")
        chain._verify_config_claim = AsyncMock(return_value="config")
        chain._verify_behavioral_claim = AsyncMock(return_value="behavioral")

        async def _route(claim_type: str):
            classification = ClaimClassification(
                claim_type=claim_type, confidence=1.0, reasoning="x"
            )
            return await chain._verify_single_model(_claim(), classification)

        assert await _route("api_signature") == "api"
        assert await _route("version_requirement") == "version"
        assert await _route("configuration") == "config"
        assert await _route("behavioral") == "behavioral"

    async def test_unknown_type_falls_back_to_behavioral(self):
        chain = _chain()
        chain._verify_behavioral_claim = AsyncMock(return_value="behavioral")
        classification = ClaimClassification(claim_type="mystery", confidence=0.5, reasoning="x")
        result = await chain._verify_single_model(_claim(), classification)
        assert result == "behavioral"
        chain._verify_behavioral_claim.assert_awaited_once()
