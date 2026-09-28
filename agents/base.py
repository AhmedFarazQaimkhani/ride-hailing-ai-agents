"""Base mixin for agents."""

from core.context import AgentContext
from core.recommendations import Recommendation


class BaseAgent:
    """Base for all co-pilot agents; implements DriverAgent protocol."""

    agent_id: str = "base"

    def run(self, context: AgentContext) -> list[Recommendation]:
        """Override in subclasses."""
        return []
