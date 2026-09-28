"""Recommendation output model — unified across all agents."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class RecommendationType(str, Enum):
    MOVE = "move"
    WAIT = "wait"
    BREAK = "break"
    ACCEPT_RIDE = "accept_ride"
    SKIP_RIDE = "skip_ride"
    SWITCH_APP = "switch_app"
    PARK = "park"
    AVOID_ZONE = "avoid_zone"
    INFO = "info"


@dataclass
class Recommendation:
    """Single recommendation from any agent."""

    agent_id: str
    type: RecommendationType
    title: str
    description: str
    confidence: float  # 0.0–1.0
    reasoning: list[str] = field(default_factory=list)
    action_payload: dict[str, Any] = field(default_factory=dict)
    # For explainable coach: human-readable explanation
    explanation: Optional[str] = None
