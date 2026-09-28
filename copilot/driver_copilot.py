"""
Driver Co-Pilot — single entry point that runs all agents and returns
prioritized, explainable recommendations.
"""

from config import DEFAULT_CONFIDENCE_FLOOR

from core.context import AgentContext, DriverContext
from core.recommendations import Recommendation

from agents import (
    DemandAnticipationAgent,
    IdleTimeOptimizationAgent,
    EarningsStrategyAgent,
    ParkingSafetyAgent,
    FatigueMonitoringAgent,
    MultiAppArbitrageAgent,
    ExplainableCoachAgent,
)


class DriverCoPilot:
    """Orchestrates all co-pilot agents and merges their recommendations."""

    def __init__(self, confidence_floor: float = DEFAULT_CONFIDENCE_FLOOR):
        self.confidence_floor = confidence_floor
        self.agents = [
            DemandAnticipationAgent(),
            IdleTimeOptimizationAgent(),
            EarningsStrategyAgent(),
            ParkingSafetyAgent(),
            FatigueMonitoringAgent(),
            MultiAppArbitrageAgent(),
            ExplainableCoachAgent(),
        ]
        # Coach only enriches; doesn't run as standalone
        self._coach = ExplainableCoachAgent()

    def recommend(self, context: AgentContext) -> list[Recommendation]:
        """Run all agents, filter by confidence, enrich with explanations, sort by priority."""
        all_recs: list[Recommendation] = []
        for agent in self.agents:
            if agent.agent_id == "explainable_coach":
                continue
            recs = agent.run(context)
            all_recs.extend(recs)

        # Filter by confidence
        filtered = [r for r in all_recs if r.confidence >= self.confidence_floor]

        # Enrich with explainable coach
        for r in filtered:
            self._coach.enrich(r)

        # Sort: BREAK and AVOID_ZONE first, then MOVE/SWITCH_APP, then WAIT/INFO
        type_order = {
            "break": 0,
            "avoid_zone": 1,
            "park": 2,
            "move": 3,
            "switch_app": 4,
            "skip_ride": 5,
            "accept_ride": 6,
            "wait": 7,
            "info": 8,
        }
        filtered.sort(
            key=lambda r: (
                type_order.get(r.type.value, 9),
                -r.confidence,
            )
        )
        return filtered
