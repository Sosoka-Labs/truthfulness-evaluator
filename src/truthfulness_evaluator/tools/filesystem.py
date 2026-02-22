"""Filesystem tools for evidence gathering."""

from pathlib import Path
from typing import Optional

from langchain_core.tools import tool


def get_filesystem_tools(root_path: str):
    """Get filesystem tools scoped to a root directory."""
    
    root = Path(root_path).resolve()
    
    @tool
    def list_files(path: str = ".") -> str:
        """List files and directories at the given path.
        
        Args:
            path: Relative path from root (default: current directory)
            
        Returns:
            List of files and directories
        """
        try:
            target = (root / path).resolve()
            # Security: ensure we stay within root
            try:
                target.relative_to(root)
            except ValueError:
                return "Error: Path outside allowed directory"
            
            items = []
            for item in target.iterdir():
                item_type = "📁" if item.is_dir() else "📄"
                size = ""
                if item.is_file():
                    size_kb = item.stat().st_size / 1024
                    size = f" ({size_kb:.1f} KB)"
                items.append(f"{item_type} {item.name}{size}")
            
            return "\n".join(items) if items else "(empty directory)"
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    @tool
    def read_file(file_path: str) -> str:
        """Read the contents of a file.
        
        Args:
            file_path: Relative path to the file from root
            
        Returns:
            File contents as string
        """
        try:
            target = (root / file_path).resolve()
            # Security: ensure we stay within root
            try:
                target.relative_to(root)
            except ValueError:
                return "Error: Path outside allowed directory"
            
            if not target.exists():
                return f"Error: File not found: {file_path}"
            
            if not target.is_file():
                return f"Error: Not a file: {file_path}"
            
            # Read file with size limit
            max_size = 100 * 1024  # 100 KB limit
            content = target.read_text(encoding='utf-8', errors='ignore')
            
            if len(content) > max_size:
                content = content[:max_size] + "\n... (truncated)"
            
            return content
            
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    @tool
    def grep_files(pattern: str, file_pattern: str = "*") -> str:
        """Search for a pattern in files.
        
        Args:
            pattern: Text pattern to search for
            file_pattern: Glob pattern for files to search (default: all files)
            
        Returns:
            Matching files with line numbers and context
        """
        try:
            matches = []
            
            for file_path in root.rglob(file_pattern):
                if not file_path.is_file():
                    continue
                
                # Skip binary files
                if file_path.stat().st_size > 1024 * 1024:  # Skip files > 1MB
                    continue
                
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.split('\n')
                    
                    file_matches = []
                    for i, line in enumerate(lines, 1):
                        if pattern.lower() in line.lower():
                            # Get context (2 lines before and after)
                            start = max(0, i - 3)
                            end = min(len(lines), i + 2)
                            context = '\n'.join(f"{j+1}: {lines[j]}" for j in range(start, end))
                            file_matches.append(f"Line {i}:\n{context}")
                    
                    if file_matches:
                        rel_path = file_path.relative_to(root)
                        matches.append(f"📄 {rel_path}:\n" + '\n---\n'.join(file_matches[:3]))  # Max 3 matches per file
                        
                except Exception:
                    continue
            
            if not matches:
                return f"No matches found for '{pattern}'"
            
            return '\n\n'.join(matches[:10])  # Max 10 files
            
        except Exception as e:
            return f"Error searching: {str(e)}"
    
    @tool
    def find_related_files(file_path: str) -> str:
        """Find files related to the given file (imports, references, etc.).
        
        Args:
            file_path: Path to the reference file
            
        Returns:
            List of related files
        """
        try:
            target = (root / file_path).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                return "Error: Path outside allowed directory"
            
            if not target.exists():
                return f"Error: File not found: {file_path}"
            
            content = target.read_text(encoding='utf-8', errors='ignore')
            related = []
            
            # Look for common reference patterns
            import re
            
            # Python imports
            python_imports = re.findall(r'(?:from|import)\s+(\S+)', content)
            for imp in python_imports[:10]:
                # Convert import to potential file path
                parts = imp.split('.')
                potential_path = root / (parts[0] + ".py")
                if potential_path.exists() and potential_path != target:
                    related.append(f"🐍 Python import: {potential_path.relative_to(root)}")
            
            # Markdown links
            md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            for text, link in md_links[:10]:
                if not link.startswith(('http://', 'https://', '#')):
                    potential_path = (target.parent / link).resolve()
                    if str(potential_path).startswith(str(root)) and potential_path.exists():
                        related.append(f"🔗 Link: {potential_path.relative_to(root)}")
            
            if not related:
                return "No related files found"
            
            return '\n'.join(related[:20])
            
        except Exception as e:
            return f"Error finding related files: {str(e)}"
    
    return [list_files, read_file, grep_files, find_related_files]
