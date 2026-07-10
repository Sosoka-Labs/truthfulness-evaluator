"""Tests for the filesystem evidence tools.

These tools are pure stdlib (pathlib/re) closures scoped to a root directory,
so they are exercised directly against a ``tmp_path`` tree with no mocking.
Tools are LangChain ``StructuredTool`` objects; ``.func(...)`` invokes the
underlying callable.
"""

from pathlib import Path

from truthfulness_evaluator.evidence.tools.filesystem import get_filesystem_tools


def _tools(root: Path):
    """Return the four filesystem tools mapped by name for a given root."""
    return {t.name: t for t in get_filesystem_tools(str(root))}


# =============================================================================
# list_files
# =============================================================================


class TestListFiles:
    def test_empty_directory(self, tmp_path: Path):
        result = _tools(tmp_path)["list_files"].func(".")
        assert result == "(empty directory)"

    def test_lists_files_and_dirs_with_metadata(self, tmp_path: Path):
        (tmp_path / "notes.txt").write_text("hello")
        (tmp_path / "subdir").mkdir()
        result = _tools(tmp_path)["list_files"].func(".")
        assert "📄 notes.txt" in result
        assert "KB)" in result  # file size rendered
        assert "📁 subdir" in result

    def test_path_traversal_blocked(self, tmp_path: Path):
        result = _tools(tmp_path)["list_files"].func("../../..")
        assert result == "Error: Path outside allowed directory"


# =============================================================================
# read_file
# =============================================================================


class TestReadFile:
    def test_reads_contents(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("line one\nline two")
        result = _tools(tmp_path)["read_file"].func("a.txt")
        assert result == "line one\nline two"

    def test_missing_file(self, tmp_path: Path):
        result = _tools(tmp_path)["read_file"].func("nope.txt")
        assert result == "Error: File not found: nope.txt"

    def test_directory_is_not_a_file(self, tmp_path: Path):
        (tmp_path / "adir").mkdir()
        result = _tools(tmp_path)["read_file"].func("adir")
        assert result == "Error: Not a file: adir"

    def test_truncates_beyond_100kb(self, tmp_path: Path):
        (tmp_path / "big.txt").write_text("x" * (100 * 1024 + 500))
        result = _tools(tmp_path)["read_file"].func("big.txt")
        assert result.endswith("... (truncated)")
        assert len(result) <= 100 * 1024 + len("\n... (truncated)")

    def test_path_traversal_blocked(self, tmp_path: Path):
        result = _tools(tmp_path)["read_file"].func("../../../etc/hosts")
        assert result == "Error: Path outside allowed directory"


# =============================================================================
# grep_files
# =============================================================================


class TestGrepFiles:
    def test_case_insensitive_match(self, tmp_path: Path):
        (tmp_path / "doc.txt").write_text("The PYTHON language\n")
        result = _tools(tmp_path)["grep_files"].func("python")
        assert "doc.txt" in result
        assert "The PYTHON language" in result

    def test_returns_surrounding_context(self, tmp_path: Path):
        lines = [f"line {n}" for n in range(1, 11)]
        lines[4] = "needle here"  # line 5 (1-indexed)
        (tmp_path / "ctx.txt").write_text("\n".join(lines))
        result = _tools(tmp_path)["grep_files"].func("needle")
        # ±2 lines of context around the match are included
        assert "3: line 3" in result
        assert "5: needle here" in result
        assert "7: line 7" in result

    def test_no_matches(self, tmp_path: Path):
        (tmp_path / "doc.txt").write_text("nothing relevant")
        result = _tools(tmp_path)["grep_files"].func("absent")
        assert result == "No matches found for 'absent'"

    def test_skips_files_over_one_mb(self, tmp_path: Path):
        (tmp_path / "huge.txt").write_text("needle\n" + "x" * (1024 * 1024 + 10))
        result = _tools(tmp_path)["grep_files"].func("needle")
        assert result == "No matches found for 'needle'"

    def test_caps_at_three_matches_per_file(self, tmp_path: Path):
        (tmp_path / "many.txt").write_text("\n".join(["hit"] * 6))
        result = _tools(tmp_path)["grep_files"].func("hit")
        # Each rendered match block is labelled "Line N:"; capped at 3 per file.
        assert result.count("Line ") == 3

    def test_respects_file_pattern_glob(self, tmp_path: Path):
        (tmp_path / "match.py").write_text("token")
        (tmp_path / "skip.txt").write_text("token")
        result = _tools(tmp_path)["grep_files"].func("token", "*.py")
        assert "match.py" in result
        assert "skip.txt" not in result


# =============================================================================
# find_related_files
# =============================================================================


class TestFindRelatedFiles:
    def test_resolves_python_imports(self, tmp_path: Path):
        (tmp_path / "helper.py").write_text("VALUE = 1\n")
        (tmp_path / "main.py").write_text("import helper\n")
        result = _tools(tmp_path)["find_related_files"].func("main.py")
        assert "helper.py" in result

    def test_resolves_markdown_links(self, tmp_path: Path):
        (tmp_path / "target.md").write_text("# Target\n")
        (tmp_path / "index.md").write_text("See [the target](target.md).\n")
        result = _tools(tmp_path)["find_related_files"].func("index.md")
        assert "target.md" in result

    def test_ignores_external_links(self, tmp_path: Path):
        (tmp_path / "index.md").write_text("See [site](https://example.com).\n")
        result = _tools(tmp_path)["find_related_files"].func("index.md")
        assert result == "No related files found"

    def test_missing_reference_file(self, tmp_path: Path):
        result = _tools(tmp_path)["find_related_files"].func("ghost.py")
        assert result == "Error: File not found: ghost.py"

    def test_path_traversal_blocked(self, tmp_path: Path):
        result = _tools(tmp_path)["find_related_files"].func("../../secret.py")
        assert result == "Error: Path outside allowed directory"


def test_all_tools_return_strings_on_error(tmp_path: Path):
    """Every tool degrades to a string message rather than raising."""
    tools = _tools(tmp_path)
    assert isinstance(tools["list_files"].func("../.."), str)
    assert isinstance(tools["read_file"].func("missing"), str)
    assert isinstance(tools["grep_files"].func("x"), str)
    assert isinstance(tools["find_related_files"].func("missing"), str)
