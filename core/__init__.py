"""Shared types and context for ride-hailing driver co-pilot agents."""

from .context import DriverContext, AgentContext
from .recommendations import Recommendation, RecommendationType

__all__ = [
    "DriverContext",
    "AgentContext",
    "Recommendation",
    "RecommendationType",
]
