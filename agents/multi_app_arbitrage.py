"""
Multi-App Arbitrage Agent — for drivers on Uber, Careem, inDrive.
Compares demand signals; suggests which app to prioritize or when to switch.
"Pause Uber — Careem demand rising nearby."
"""

from core.context import AgentContext
from core.recommendations import Recommendation, RecommendationType
from .base import BaseAgent


# Mock: which app is "hot" in which hour (simulate demand shifts)
def _app_scores_for_hour(hour: int) -> list[tuple[str, float]]:
    # Placeholder: time-based mock
    if 7 <= hour <= 9:
        return [("uber", 0.9), ("careem", 0.7), ("indrive", 0.5)]
    if 17 <= hour <= 20:
        return [("careem", 0.85), ("uber", 0.8), ("indrive", 0.6)]
    return [("uber", 0.7), ("careem", 0.65), ("indrive", 0.55)]


class MultiAppArbitrageAgent(BaseAgent):
    """Suggests which app to prioritize when driver runs multiple platforms."""

    agent_id = "multi_app_arbitrage"

    def run(self, context: AgentContext) -> list[Recommendation]:
        driver = context.driver
        if driver.is_on_ride or len(driver.apps_enabled) < 2:
            return []

        current = driver.current_app or driver.apps_enabled[0]
        hour = driver.current_time.hour
        scores = _app_scores_for_hour(hour)
        enabled_scores = [(app, s) for app, s in scores if app in driver.apps_enabled]
        if not enabled_scores:
            return []

        best_app, best_score = enabled_scores[0]
        current_score = next((s for a, s in enabled_scores if a == current), 0.0)

        if best_app != current and best_score - current_score >= 0.1:
            return [
                Recommendation(
                    agent_id=self.agent_id,
                    type=RecommendationType.SWITCH_APP,
                    title=f"Prioritize {best_app.title()}",
                    description=f"Demand on {best_app.title()} is rising relative to {current.title()}. Switch focus to get more pings.",
                    confidence=0.68,
                    reasoning=[
                        f"Demand signal for {best_app} is ~{int((best_score - current_score) * 100)}% higher in this window.",
                        "Time-of-day pattern favors this app in your area.",
                    ],
                    action_payload={"suggested_app": best_app, "current_app": current},
                )
            ]
        return []
