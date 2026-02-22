"""Enhanced filesystem tools inspired by DeepAgent patterns."""

from pathlib import Path

from langchain_core.tools import tool


class EnhancedFilesystemTools:
    """Enhanced filesystem tools with DeepAgent-inspired patterns."""

    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()

    def get_tools(self):
        """Get all filesystem tools."""
        return [
            self.list_files,
            self.read_file,
            self.read_file_chunk,
            self.grep_files,
            self.find_function,
            self.find_class,
        ]

    @tool
    def list_files(self, path: str = ".", pattern: str = "*") -> str:
        """List files and directories with metadata.

        Args:
            path: Relative path from root (default: current directory)
            pattern: Glob pattern to filter files (default: all)
        """
        try:
            target = (self.root / path).resolve()
            try:
                target.relative_to(self.root)
            except ValueError:
                return "Error: Path outside allowed directory"

            items = []
            for item in target.glob(pattern):
                if item.is_dir():
                    items.append(f"📁 {item.name}/")
                else:
                    size_kb = item.stat().st_size / 1024
                    items.append(f"📄 {item.name} ({size_kb:.1f} KB)")

            return "\n".join(sorted(items)) if items else "(empty)"
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def read_file(self, file_path: str) -> str:
        """Read entire file content.

        Args:
            file_path: Relative path to file from root
        """
        try:
            target = (self.root / file_path).resolve()
            try:
                target.relative_to(self.root)
            except ValueError:
                return "Error: Path outside allowed directory"

            if not target.exists():
                return f"Error: File not found: {file_path}"

            content = target.read_text(encoding="utf-8", errors="ignore")

            # Add line numbers
            lines = content.split("\n")
            numbered = [f"{i+1:4d}: {line}" for i, line in enumerate(lines)]

            return "\n".join(numbered)
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def read_file_chunk(self, file_path: str, offset: int = 0, limit: int = 50) -> str:
        """Read a chunk of a file with line numbers (prevents context overflow).

        Args:
            file_path: Relative path to file from root
            offset: Starting line number (0-indexed)
            limit: Maximum number of lines to read (default: 50)
        """
        try:
            target = (self.root / file_path).resolve()
            try:
                target.relative_to(self.root)
            except ValueError:
                return "Error: Path outside allowed directory"

            if not target.exists():
                return f"Error: File not found: {file_path}"

            content = target.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")

            # Get chunk
            start = offset
            end = min(offset + limit, len(lines))
            selected = lines[start:end]

            # Add line numbers
            numbered = [f"{i+1:4d}: {line}" for i, line in enumerate(selected)]

            # Add truncation notice
            if end < len(lines):
                numbered.append(f"      ... ({len(lines) - end} more lines)")

            header = f"=== {file_path} (lines {start+1}-{end} of {len(lines)}) ===\n"
            return header + "\n".join(numbered)
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def grep_files(self, pattern: str, file_pattern: str = "*.py", max_results: int = 10) -> str:
        """Search for pattern in files using grep.

        Args:
            pattern: Text pattern to search for
            file_pattern: Glob pattern for files to search (default: *.py)
            max_results: Maximum number of results to return (default: 10)
        """
        try:
            results = []

            for file_path in self.root.rglob(file_pattern):
                if not file_path.is_file():
                    continue
                if ".venv" in str(file_path) or "__pycache__" in str(file_path):
                    continue
                if file_path.stat().st_size > 1024 * 1024:  # Skip files > 1MB
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    lines = content.split("\n")

                    file_matches = []
                    for i, line in enumerate(lines, 1):
                        if pattern.lower() in line.lower():
                            # Get context
                            context_start = max(0, i - 2)
                            context_end = min(len(lines), i + 1)
                            context = "\n".join(
                                f"{j+1:4d}: {lines[j]}" for j in range(context_start, context_end)
                            )
                            file_matches.append(f"Line {i}:\n{context}")

                    if file_matches:
                        rel_path = file_path.relative_to(self.root)
                        results.append(f"📄 {rel_path}:\n" + "\n---\n".join(file_matches[:2]))

                    if len(results) >= max_results:
                        break

                except Exception:
                    continue

            if not results:
                return f"No matches found for '{pattern}'"

            return "\n\n".join(results)
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def find_function(self, function_name: str) -> str:
        """Find a function definition in the codebase.

        Args:
            function_name: Name of the function to find
        """
        try:
            import ast

            matches = []

            for py_file in self.root.rglob("*.py"):
                if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                    continue

                try:
                    content = py_file.read_text()
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if (
                            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and node.name == function_name
                        ):
                            # Extract function
                            lines = content.split("\n")
                            start = node.lineno - 1
                            end = node.end_lineno if hasattr(node, "end_lineno") else start + 20
                            func_lines = lines[start:end]

                            # Add line numbers
                            numbered = [
                                f"{i+1:4d}: {line}" for i, line in enumerate(func_lines, start)
                            ]

                            rel_path = py_file.relative_to(self.root)
                            matches.append(f"=== {rel_path} ===\n" + "\n".join(numbered))
                            break

                    if len(matches) >= 3:  # Limit results
                        break

                except SyntaxError:
                    continue
                except Exception:
                    continue

            if not matches:
                return f"Function '{function_name}' not found"

            return "\n\n".join(matches)
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def find_class(self, class_name: str) -> str:
        """Find a class definition in the codebase.

        Args:
            class_name: Name of the class to find
        """
        try:
            import ast

            matches = []

            for py_file in self.root.rglob("*.py"):
                if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                    continue

                try:
                    content = py_file.read_text()
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef) and node.name == class_name:
                            # Extract class
                            lines = content.split("\n")
                            start = node.lineno - 1
                            end = node.end_lineno if hasattr(node, "end_lineno") else start + 50
                            class_lines = lines[start:end]

                            # Add line numbers
                            numbered = [
                                f"{i+1:4d}: {line}" for i, line in enumerate(class_lines, start)
                            ]

                            rel_path = py_file.relative_to(self.root)
                            matches.append(f"=== {rel_path} ===\n" + "\n".join(numbered))
                            break

                    if len(matches) >= 3:
                        break

                except SyntaxError:
                    continue
                except Exception:
                    continue

            if not matches:
                return f"Class '{class_name}' not found"

            return "\n\n".join(matches)
        except Exception as e:
            return f"Error: {str(e)}"


def get_enhanced_filesystem_tools(root_path: str):
    """Get enhanced filesystem tools for a root path."""
    tools = EnhancedFilesystemTools(root_path)
    return tools.get_tools()
