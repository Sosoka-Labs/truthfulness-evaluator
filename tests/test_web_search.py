"""Tests for web evidence parsing in WebEvidenceGatherer.

The network-bound tools (DuckDuckGo search, HTTP fetch) are replaced with
lightweight stubs so the deterministic URL/snippet parsing inside
``gather_evidence`` can be verified offline. The raw ``web_search``/``fetch_url``
tools themselves require the internet and are left for the e2e suite.
"""

import pytest
from truthfulness_evaluator.evidence.tools.web_search import WebEvidenceGatherer


class _StubTool:
    """Stand-in for a LangChain tool exposing ``.invoke``."""

    def __init__(self, result: str = "", exc: Exception | None = None):
        self._result = result
        self._exc = exc
        self.calls: list = []

    def invoke(self, args):
        self.calls.append(args)
        if self._exc is not None:
            raise self._exc
        return self._result


def _gatherer(search: _StubTool, fetch: _StubTool | None = None) -> WebEvidenceGatherer:
    g = WebEvidenceGatherer()
    g.search_tool = search
    g.fetch_tool = fetch if fetch is not None else _StubTool(exc=RuntimeError("no fetch"))
    return g


class TestGatherEvidence:
    async def test_extracts_urls_as_evidence(self):
        search = _StubTool(
            "Python is great https://python.org and fast https://docs.python.org here"
        )
        g = _gatherer(search, fetch=_StubTool(exc=RuntimeError("skip fetch")))
        evidence = await g.gather_evidence("python speed", max_results=3)
        sources = [e["source"] for e in evidence]
        assert any("python.org" in s for s in sources)
        assert all(e["source_type"] == "web" for e in evidence)

    async def test_no_url_fallback_uses_whole_result(self):
        search = _StubTool("plain text answer with no links at all")
        g = _gatherer(search)
        evidence = await g.gather_evidence("some claim")
        assert len(evidence) == 1
        assert evidence[0]["source"] == "duckduckgo_search"
        assert evidence[0]["relevance"] == 0.5

    async def test_search_failure_returns_error_entry(self):
        g = _gatherer(_StubTool(exc=RuntimeError("boom")))
        evidence = await g.gather_evidence("claim")
        assert evidence == [{"error": "Search failed: boom"}]

    async def test_successful_fetch_enriches_top_result(self):
        search = _StubTool("See https://example.com/page for details")
        fetch = _StubTool("The full fetched article body.")
        g = _gatherer(search, fetch)
        evidence = await g.gather_evidence("claim")
        assert evidence[0]["fetched"] is True
        assert evidence[0]["relevance"] == 0.8
        assert "full fetched article" in evidence[0]["content"]

    async def test_fetch_error_keeps_snippet(self):
        search = _StubTool("Context here https://example.com/page trailing")
        fetch = _StubTool(exc=RuntimeError("network down"))
        g = _gatherer(search, fetch)
        evidence = await g.gather_evidence("claim")
        assert evidence[0]["fetched"] is False
        assert evidence[0]["relevance"] == 0.6

    async def test_fetch_returning_error_string_is_not_applied(self):
        search = _StubTool("Context here https://example.com/page trailing")
        fetch = _StubTool("Error fetching URL: timeout")
        g = _gatherer(search, fetch)
        evidence = await g.gather_evidence("claim")
        # Error-prefixed fetch output must not overwrite the snippet.
        assert evidence[0]["fetched"] is False

    async def test_long_snippet_is_truncated(self):
        long_prefix = "A" * 800
        search = _StubTool(f"{long_prefix} https://example.com/x end")
        g = _gatherer(search, fetch=_StubTool(exc=RuntimeError("skip")))
        evidence = await g.gather_evidence("claim")
        assert len(evidence[0]["content"]) <= 600


@pytest.mark.parametrize("num", [1, 2])
async def test_respects_max_results(num: int):
    search = _StubTool("a https://one.com b https://two.com c https://three.com d")
    g = _gatherer(search, fetch=_StubTool(exc=RuntimeError("skip")))
    evidence = await g.gather_evidence("claim", max_results=num)
    assert len(evidence) == num
