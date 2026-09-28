"""Protocol that all agents implement."""

from typing import Protocol

from .context import AgentContext
from .recommendations import Recommendation


class DriverAgent(Protocol):
    """Interface for every co-pilot agent."""

    @property
    def agent_id(self) -> str:
        """Unique identifier for this agent."""
        ...

    def run(self, context: AgentContext) -> list[Recommendation]:
        """Produce zero or more recommendations given current context."""
        ...
