"""
Fatigue & Stress Monitoring Agent — continuous driving time, break patterns.
"Your earnings drop after 3.5 hours — take a 15-min break."
"""

from core.context import AgentContext
from core.recommendations import Recommendation, RecommendationType
from .base import BaseAgent


class FatigueMonitoringAgent(BaseAgent):
    """Monitors session length and break patterns; nudges for rest."""

    agent_id = "fatigue_monitoring"

    # Thresholds (mins)
    CONTINUOUS_DRIVING_WARN = 120   # 2 hours
    CONTINUOUS_DRIVING_URGENT = 210  # 3.5 hours
    SUGGESTED_BREAK_MINS = 15

    def run(self, context: AgentContext) -> list[Recommendation]:
        driver = context.driver
        recs = []
        continuous = driver.continuous_driving_minutes

        if continuous >= self.CONTINUOUS_DRIVING_URGENT:
            recs.append(
                Recommendation(
                    agent_id=self.agent_id,
                    type=RecommendationType.BREAK,
                    title="Take a 15-minute break",
                    description="You've been driving for over 3.5 hours. Your earnings and safety drop after this point. Park and rest for 15 mins.",
                    confidence=0.92,
                    reasoning=[
                        "Continuous driving > 3.5 hrs correlates with lower acceptance quality.",
                        "Fatigue increases accident risk.",
                    ],
                    action_payload={"break_mins": self.SUGGESTED_BREAK_MINS, "priority": "high"},
                )
            )
        elif continuous >= self.CONTINUOUS_DRIVING_WARN:
            recs.append(
                Recommendation(
                    agent_id=self.agent_id,
                    type=RecommendationType.BREAK,
                    title="Consider a short break soon",
                    description="You've been driving ~2 hours without a break. A 10–15 min rest in the next 30 mins can help maintain earnings and focus.",
                    confidence=0.75,
                    reasoning=[
                        "Data shows earnings dip after ~2.5 hrs without break.",
                        "Short breaks improve subsequent acceptance rates.",
                    ],
                    action_payload={"break_mins": 10, "priority": "medium"},
                )
            )

        return recs
