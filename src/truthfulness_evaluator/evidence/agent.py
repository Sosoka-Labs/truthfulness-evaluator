"""Filesystem evidence gathering agent using LangGraph 1.0+ patterns."""

import json
import re
from typing import Any

from langgraph.prebuilt import create_react_agent

from ..core.logging_config import get_logger
from ..llm import create_chat_model
from .tools.filesystem import get_filesystem_tools

logger = get_logger()


class FilesystemEvidenceAgent:
    """ReAct agent for filesystem evidence gathering using LangGraph 1.0+."""

    def __init__(self, root_path: str, model: str = "gpt-4o"):
        """Initialize the agent.

        Args:
            root_path: Root directory to search for evidence
            model: Model name (e.g., "gpt-4o", "claude-3-5-sonnet-20241022")
        """
        self.root_path = root_path
        self.model = model
        self._agent = None

    @property
    def agent(self):
        """Lazy-initialized agent instance."""
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent

    def _create_agent(self):
        """Create agent using LangGraph 1.0+ create_react_agent."""
        tools = get_filesystem_tools(self.root_path)

        llm = create_chat_model(self.model, temperature=0)

        system_prompt = """You are an evidence-gathering agent exploring a filesystem.

Your task: Find concrete evidence that SUPPORTS, REFUTES, or provides context for claims.

Instructions:
1. Use list_files to explore directories
2. Use grep_files to search for keywords from the claim
3. Use read_file to examine relevant files
4. Use find_related_files to discover connected documentation

For each piece of evidence found, provide:
- file_path: exact path to the file
- content: relevant excerpt (quote precisely, 200 chars max)
- relevance: score 0.0-1.0 (how relevant to claim)
- supports: true (supports), false (refutes), or null (neutral/context)

Format your final answer as JSON:
{"evidence": [{"file_path": "...", "content": "...", "relevance": 0.8, "supports": true}, ...]}

If no evidence found, return: {"evidence": []}"""

        return create_react_agent(llm, tools, state_modifier=system_prompt)

    async def search(self, claim: str) -> list[dict[str, Any]]:
        """Search filesystem for evidence about a claim.

        Args:
            claim: The claim text to find evidence for

        Returns:
            List of evidence dicts with keys: file_path, content, relevance, supports
        """
        prompt = f"""Find evidence for this claim: "{claim}"

Filesystem root: {self.root_path}

Search strategy:
1. Identify keywords from the claim
2. Use grep_files to locate relevant files
3. Read the most promising files
4. Extract specific quotes that relate to the claim

Return findings as JSON."""

        try:
            result = await self.agent.ainvoke({"messages": [("user", prompt)]})
            return self._parse_evidence(result)
        except Exception as e:
            logger.error(f"Evidence search failed: {e}")
            return []

    def _parse_evidence(self, result: dict) -> list[dict[str, Any]]:
        """Parse agent response into structured evidence.

        Args:
            result: Agent invocation result with messages

        Returns:
            List of evidence dictionaries
        """
        messages = result.get("messages", [])
        if not messages:
            return []

        # Get the last AI message
        final_message = messages[-1]
        content = final_message.content if hasattr(final_message, "content") else str(final_message)

        # Try to parse JSON response
        evidence = self._extract_json_evidence(content)
        if evidence:
            return evidence

        # Fallback: extract from tool call observations
        return self._extract_tool_evidence(messages)

    def _extract_json_evidence(self, content: str) -> list[dict[str, Any]]:
        """Extract evidence from JSON-formatted response."""
        try:
            # Look for JSON block
            json_match = re.search(r"\{.*\"evidence\".*\}", content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("evidence", [])
        except (json.JSONDecodeError, AttributeError):
            pass
        return []

    def _extract_tool_evidence(self, messages: list) -> list[dict[str, Any]]:
        """Fallback: extract evidence from tool call results in message history."""
        evidence = []
        seen_files = set()

        for msg in messages:
            # Look for read_file tool calls
            if hasattr(msg, "additional_kwargs"):
                tool_calls = msg.additional_kwargs.get("tool_calls", [])
                for call in tool_calls:
                    if "read_file" in str(call):
                        # Extract file path from args
                        try:
                            args = call.get("function", {}).get("arguments", "{}")
                            args_dict = json.loads(args) if isinstance(args, str) else args
                            file_path = args_dict.get("file_path", "")
                            if file_path and file_path not in seen_files:
                                seen_files.add(file_path)
                                evidence.append(
                                    {
                                        "file_path": file_path,
                                        "content": "File examined by agent",
                                        "relevance": 0.6,
                                        "supports": None,
                                    }
                                )
                        except (json.JSONDecodeError, AttributeError):
                            continue

        return evidence[:5]  # Limit to 5 items
