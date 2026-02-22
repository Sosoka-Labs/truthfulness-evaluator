"""Workflow registry with built-in presets and plugin support."""

from ...core.logging_config import get_logger
from .config import WorkflowConfig

logger = get_logger()


class WorkflowRegistry:
    """Registry for workflow configurations.

    Provides:
    - Built-in presets (external, internal, scientific, etc.)
    - Runtime registration for custom workflows
    - Entry-point discovery for third-party plugins
    """

    _workflows: dict[str, WorkflowConfig] = {}
    _discovered: bool = False

    @classmethod
    def reset(cls) -> None:
        """Reset registry state. Intended for test isolation."""
        cls._workflows.clear()
        cls._discovered = False

    @classmethod
    def register(
        cls,
        name: str,
        config: WorkflowConfig,
        *,
        override: bool = False,
    ) -> None:
        """Register a workflow configuration.

        Args:
            name: Unique workflow name.
            config: The workflow configuration.
            override: If True, allow overriding existing registrations.

        Raises:
            ValueError: If name is already registered and override is False.
        """
        if name in cls._workflows and not override:
            raise ValueError(f"Workflow '{name}' is already registered")
        cls._workflows[name] = config

    @classmethod
    def get(cls, name: str) -> WorkflowConfig:
        """Get a workflow configuration by name.

        Args:
            name: Workflow name.

        Returns:
            The WorkflowConfig.

        Raises:
            KeyError: If workflow name is not registered.
        """
        cls._discover_plugins()
        if name not in cls._workflows:
            available = ", ".join(sorted(cls._workflows.keys()))
            raise KeyError(f"Unknown workflow '{name}'. Available: {available}")
        return cls._workflows[name]

    @classmethod
    def list_workflows(cls) -> dict[str, str]:
        """List all registered workflows with descriptions.

        Returns:
            Dict of name -> description.
        """
        cls._discover_plugins()
        return {name: config.description for name, config in sorted(cls._workflows.items())}

    @classmethod
    def _discover_plugins(cls) -> None:
        """Discover workflows from entry points (lazy, one-time)."""
        if cls._discovered:
            return
        cls._discovered = True

        try:
            from importlib.metadata import entry_points

            eps = entry_points(group="truthfulness_evaluator.workflows")
            for ep in eps:
                try:
                    config = ep.load()
                    if isinstance(config, WorkflowConfig):
                        cls.register(ep.name, config)
                except Exception as e:
                    logger.warning(f"Failed to load workflow plugin '{ep.name}': {e}")
        except Exception as e:
            logger.debug(f"Entry point discovery not available: {e}")
