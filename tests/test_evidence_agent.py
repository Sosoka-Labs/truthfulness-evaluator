"""Tests for FilesystemEvidenceAgent response parsing.

Only the deterministic parsing surface is exercised here — the ReAct agent
itself (which needs an LLM) is never instantiated. ``__init__`` is lazy, so an
agent can be constructed and its pure ``_extract_*`` / ``_parse_*`` helpers
called directly.
"""

from langchain_core.messages import AIMessage
from truthfulness_evaluator.evidence.agent import FilesystemEvidenceAgent


def _agent() -> FilesystemEvidenceAgent:
    return FilesystemEvidenceAgent(root_path=".", model="gpt-4o")


def _tool_call(file_path: str) -> dict:
    """Build an OpenAI-style read_file tool call as it appears on a message."""
    return {
        "id": "call_1",
        "type": "function",
        "function": {"name": "read_file", "arguments": f'{{"file_path": "{file_path}"}}'},
    }


class TestInit:
    def test_stores_config_and_is_lazy(self):
        agent = FilesystemEvidenceAgent(root_path="/some/root", model="claude-sonnet-4-5")
        assert agent.root_path == "/some/root"
        assert agent.model == "claude-sonnet-4-5"
        assert agent._agent is None


class TestExtractJsonEvidence:
    def test_valid_json(self):
        content = '{"evidence": [{"file_path": "a.py", "relevance": 0.9, "supports": true}]}'
        result = _agent()._extract_json_evidence(content)
        assert len(result) == 1
        assert result[0]["file_path"] == "a.py"

    def test_json_embedded_in_prose(self):
        content = 'Here is my answer:\n{"evidence": [{"file_path": "b.py"}]}\nDone.'
        result = _agent()._extract_json_evidence(content)
        assert result == [{"file_path": "b.py"}]

    def test_invalid_json_returns_empty(self):
        result = _agent()._extract_json_evidence('{"evidence": [not valid]}')
        assert result == []

    def test_missing_evidence_key_returns_empty(self):
        result = _agent()._extract_json_evidence('{"other": "data"}')
        assert result == []

    def test_empty_evidence_array(self):
        assert _agent()._extract_json_evidence('{"evidence": []}') == []

    def test_no_json_at_all(self):
        assert _agent()._extract_json_evidence("no json here") == []


class TestExtractToolEvidence:
    def test_single_read_file_call(self):
        msg = AIMessage(content="", additional_kwargs={"tool_calls": [_tool_call("src/x.py")]})
        result = _agent()._extract_tool_evidence([msg])
        assert result == [
            {
                "file_path": "src/x.py",
                "content": "File examined by agent",
                "relevance": 0.6,
                "supports": None,
            }
        ]

    def test_deduplicates_repeated_files(self):
        calls = [_tool_call("dup.py"), _tool_call("dup.py"), _tool_call("other.py")]
        msg = AIMessage(content="", additional_kwargs={"tool_calls": calls})
        result = _agent()._extract_tool_evidence([msg])
        paths = [e["file_path"] for e in result]
        assert paths == ["dup.py", "other.py"]

    def test_caps_at_five(self):
        calls = [_tool_call(f"f{n}.py") for n in range(8)]
        msg = AIMessage(content="", additional_kwargs={"tool_calls": calls})
        result = _agent()._extract_tool_evidence([msg])
        assert len(result) == 5

    def test_message_without_additional_kwargs_skipped(self):
        # A plain object lacking additional_kwargs must not raise.
        result = _agent()._extract_tool_evidence([object()])
        assert result == []

    def test_bad_arguments_json_skipped(self):
        bad = {"function": {"name": "read_file", "arguments": "{not json}"}}
        msg = AIMessage(content="", additional_kwargs={"tool_calls": [bad]})
        assert _agent()._extract_tool_evidence([msg]) == []


class TestParseEvidence:
    def test_json_response_takes_priority(self):
        msg = AIMessage(content='{"evidence": [{"file_path": "json.py"}]}')
        result = _agent()._parse_evidence({"messages": [msg]})
        assert result == [{"file_path": "json.py"}]

    def test_falls_back_to_tool_evidence(self):
        # Final message carries no JSON, but an earlier one has a read_file call.
        tool_msg = AIMessage(
            content="", additional_kwargs={"tool_calls": [_tool_call("fallback.py")]}
        )
        final_msg = AIMessage(content="I could not format JSON.")
        result = _agent()._parse_evidence({"messages": [tool_msg, final_msg]})
        assert result[0]["file_path"] == "fallback.py"

    def test_empty_messages(self):
        assert _agent()._parse_evidence({"messages": []}) == []
