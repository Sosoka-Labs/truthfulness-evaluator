"""Agent implementations."""

# Lazy import to prevent cascade failures during development
__all__ = ["FilesystemEvidenceAgent"]


def __getattr__(name: str):
    """Lazy load agents on first access."""
    if name == "FilesystemEvidenceAgent":
        from .evidence_agent import FilesystemEvidenceAgent

        return FilesystemEvidenceAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
