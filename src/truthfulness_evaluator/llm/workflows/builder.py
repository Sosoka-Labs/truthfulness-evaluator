"""Workflow builder for constructing LangGraph state machines."""

from .config import WorkflowConfig


class WorkflowBuilder:
    """Builds LangGraph state machines from workflow configurations.

    Phase 3 will implement the build() method that constructs a parameterized
    StateGraph by plugging strategy instances into a fixed pipeline template.

    The pipeline structure (extract -> gather -> verify loop -> report) is
    always the same. The node implementations delegate to the strategy instances.
    """

    @classmethod
    def build(cls, config: WorkflowConfig):
        """Build a compiled LangGraph from a workflow configuration.

        Args:
            config: The workflow configuration.

        Returns:
            CompiledGraph ready for execution.

        Raises:
            NotImplementedError: Phase 3 will implement this.
        """
        raise NotImplementedError(
            "WorkflowBuilder.build() will be implemented in Phase 3. "
            "This stub exists to establish the interface for Phase 1."
        )
