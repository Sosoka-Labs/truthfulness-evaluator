"""Tests for the enhanced (DeepAgent-style) filesystem tools.

These tools add line-numbered reads, chunked paging, and AST-based
function/class lookup. They are pure stdlib (pathlib/ast) and tested against a
``tmp_path`` tree.

NOTE: ``@tool`` is applied to instance methods that still declare ``self``, so
``self`` leaks into each tool's argument schema and ``.invoke({...})`` raises
"got multiple values for argument 'self'". The underlying callable is therefore
invoked directly via ``.func(instance, ...)``. This is a known design smell in
the source, not a test artifact.
"""

from pathlib import Path

from truthfulness_evaluator.evidence.tools.enhanced_filesystem import (
    EnhancedFilesystemTools,
    get_enhanced_filesystem_tools,
)


def _tools(root: Path):
    """Return (instance, {name: tool}) for a given root."""
    inst = EnhancedFilesystemTools(str(root))
    return inst, {t.name: t for t in inst.get_tools()}


# =============================================================================
# list_files
# =============================================================================


class TestListFiles:
    def test_glob_pattern_filters(self, tmp_path: Path):
        (tmp_path / "keep.py").write_text("x")
        (tmp_path / "drop.txt").write_text("x")
        inst, tools = _tools(tmp_path)
        result = tools["list_files"].func(inst, ".", "*.py")
        assert "keep.py" in result
        assert "drop.txt" not in result

    def test_sorted_output_with_dir_and_file_markers(self, tmp_path: Path):
        (tmp_path / "b.py").write_text("x")
        (tmp_path / "adir").mkdir()
        inst, tools = _tools(tmp_path)
        result = tools["list_files"].func(inst, ".", "*")
        assert "📁 adir/" in result
        assert "📄 b.py" in result
        # sorted() places the folder entry before the file entry
        assert result.index("adir") < result.index("b.py")

    def test_empty_match(self, tmp_path: Path):
        inst, tools = _tools(tmp_path)
        assert tools["list_files"].func(inst, ".", "*.md") == "(empty)"


# =============================================================================
# read_file
# =============================================================================


class TestReadFile:
    def test_line_numbered(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("first\nsecond")
        inst, tools = _tools(tmp_path)
        result = tools["read_file"].func(inst, "a.py")
        assert "   1: first" in result
        assert "   2: second" in result

    def test_missing_file(self, tmp_path: Path):
        inst, tools = _tools(tmp_path)
        assert tools["read_file"].func(inst, "ghost.py") == "Error: File not found: ghost.py"

    def test_path_traversal_blocked(self, tmp_path: Path):
        inst, tools = _tools(tmp_path)
        assert tools["read_file"].func(inst, "../../x") == "Error: Path outside allowed directory"


# =============================================================================
# read_file_chunk
# =============================================================================


class TestReadFileChunk:
    def test_offset_and_limit_slice(self, tmp_path: Path):
        (tmp_path / "f.py").write_text("\n".join(f"line{n}" for n in range(1, 21)))
        inst, tools = _tools(tmp_path)
        result = tools["read_file_chunk"].func(inst, "f.py", offset=5, limit=3)
        assert "line6" in result
        assert "line8" in result
        assert "line9" not in result

    def test_truncation_notice(self, tmp_path: Path):
        (tmp_path / "f.py").write_text("\n".join(f"line{n}" for n in range(1, 21)))
        inst, tools = _tools(tmp_path)
        result = tools["read_file_chunk"].func(inst, "f.py", offset=0, limit=5)
        assert "... (15 more lines)" in result

    def test_header_reports_range(self, tmp_path: Path):
        (tmp_path / "f.py").write_text("\n".join(f"line{n}" for n in range(1, 21)))
        inst, tools = _tools(tmp_path)
        result = tools["read_file_chunk"].func(inst, "f.py", offset=0, limit=5)
        assert "=== f.py (lines 1-5 of 20) ===" in result

    def test_offset_beyond_eof_is_graceful(self, tmp_path: Path):
        (tmp_path / "f.py").write_text("only\ntwo")
        inst, tools = _tools(tmp_path)
        result = tools["read_file_chunk"].func(inst, "f.py", offset=100, limit=5)
        # no rows, no truncation notice, but a header is still returned
        assert "===" in result
        assert "more lines" not in result


# =============================================================================
# grep_files
# =============================================================================


class TestGrepFiles:
    def test_skips_venv_and_pycache(self, tmp_path: Path):
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "lib.py").write_text("token")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "c.py").write_text("token")
        (tmp_path / "real.py").write_text("token")
        inst, tools = _tools(tmp_path)
        result = tools["grep_files"].func(inst, "token", "*.py")
        assert "real.py" in result
        assert ".venv" not in result
        assert "__pycache__" not in result

    def test_two_matches_per_file_cap(self, tmp_path: Path):
        (tmp_path / "m.py").write_text("\n".join(["hit"] * 5))
        inst, tools = _tools(tmp_path)
        result = tools["grep_files"].func(inst, "hit", "*.py")
        assert result.count("Line ") == 2

    def test_max_results_limit(self, tmp_path: Path):
        for n in range(5):
            (tmp_path / f"f{n}.py").write_text("hit")
        inst, tools = _tools(tmp_path)
        result = tools["grep_files"].func(inst, "hit", "*.py", max_results=2)
        assert result.count("📄") == 2

    def test_no_matches(self, tmp_path: Path):
        (tmp_path / "f.py").write_text("nothing")
        inst, tools = _tools(tmp_path)
        assert tools["grep_files"].func(inst, "absent", "*.py") == "No matches found for 'absent'"


# =============================================================================
# find_function (AST)
# =============================================================================


class TestFindFunction:
    def test_finds_sync_and_async(self, tmp_path: Path):
        (tmp_path / "s.py").write_text("def target():\n    return 1\n")
        (tmp_path / "a.py").write_text("async def target():\n    return 2\n")
        inst, tools = _tools(tmp_path)
        result = tools["find_function"].func(inst, "target")
        assert "s.py" in result or "a.py" in result
        assert "target" in result

    def test_reports_line_numbers(self, tmp_path: Path):
        (tmp_path / "s.py").write_text("# header\n\ndef target():\n    return 1\n")
        inst, tools = _tools(tmp_path)
        result = tools["find_function"].func(inst, "target")
        assert "3:" in result  # def is on line 3

    def test_syntax_error_file_skipped(self, tmp_path: Path):
        (tmp_path / "broken.py").write_text("def (:\n")
        (tmp_path / "good.py").write_text("def target():\n    return 1\n")
        inst, tools = _tools(tmp_path)
        result = tools["find_function"].func(inst, "target")
        assert "good.py" in result

    def test_not_found(self, tmp_path: Path):
        (tmp_path / "s.py").write_text("def other():\n    pass\n")
        inst, tools = _tools(tmp_path)
        assert tools["find_function"].func(inst, "missing") == "Function 'missing' not found"

    def test_limits_to_three_matches(self, tmp_path: Path):
        for n in range(5):
            (tmp_path / f"f{n}.py").write_text("def target():\n    return 1\n")
        inst, tools = _tools(tmp_path)
        result = tools["find_function"].func(inst, "target")
        assert result.count(".py ===") == 3  # one header per match, capped at 3


# =============================================================================
# find_class (AST)
# =============================================================================


class TestFindClass:
    def test_finds_multiline_class(self, tmp_path: Path):
        (tmp_path / "c.py").write_text("class Widget:\n    x = 1\n    y = 2\n")
        inst, tools = _tools(tmp_path)
        result = tools["find_class"].func(inst, "Widget")
        assert "c.py" in result
        assert "class Widget" in result

    def test_not_found(self, tmp_path: Path):
        (tmp_path / "c.py").write_text("class Other:\n    pass\n")
        inst, tools = _tools(tmp_path)
        assert tools["find_class"].func(inst, "Missing") == "Class 'Missing' not found"

    def test_limits_to_three_matches(self, tmp_path: Path):
        for n in range(5):
            (tmp_path / f"c{n}.py").write_text("class Widget:\n    pass\n")
        inst, tools = _tools(tmp_path)
        result = tools["find_class"].func(inst, "Widget")
        assert result.count(".py ===") == 3  # one header per match, capped at 3


def test_factory_returns_six_tools(tmp_path: Path):
    tools = get_enhanced_filesystem_tools(str(tmp_path))
    assert len(tools) == 6
    assert {t.name for t in tools} == {
        "list_files",
        "read_file",
        "read_file_chunk",
        "grep_files",
        "find_function",
        "find_class",
    }
