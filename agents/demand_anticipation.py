"""
Demand Anticipation Agent — predicts where demand WILL be, not where it was.
Proactive: "In 12 minutes, demand will spike near Mall X — move now."
Uses LLM when OPENAI_API_KEY is set; otherwise rule-based.
"""

from core.context import AgentContext, Location
from core.recommendations import Recommendation, RecommendationType
from core.llm import ask_agent, context_snapshot, is_available
from .base import BaseAgent

# Zone name -> (lat, lng, label) for mapping LLM output
_ZONES = {
    "mall of emirates": (25.1193, 55.1993, "Mall of Emirates"),
    "dubai marina": (25.0800, 55.1390, "Dubai Marina"),
    "marina": (25.0800, 55.1390, "Dubai Marina"),
    "downtown dubai": (25.1972, 55.2744, "Downtown Dubai"),
    "downtown": (25.1972, 55.2744, "Downtown Dubai"),
    "airport": (25.2532, 55.3644, "Airport T1"),
    "airport t1": (25.2532, 55.3644, "Airport T1"),
    "jbr": (25.0784, 55.1292, "JBR"),
}


class DemandAnticipationAgent(BaseAgent):
    """Predicts future demand hotspots using time, events, weather, traffic. LLM or rules."""

    agent_id = "demand_anticipation"

    _HOTSPOTS = [
        ("Mall of Emirates", 25.1193, 55.1993, 12, 1.4),
        ("Dubai Marina", 25.0800, 55.1390, 15, 1.35),
        ("Downtown Dubai", 25.1972, 55.2744, 8, 1.5),
        ("Airport T1", 25.2532, 55.3644, 25, 1.2),
        ("JBR", 25.0784, 55.1292, 10, 1.3),
    ]

    def _run_with_llm(self, context: AgentContext) -> list[Recommendation]:
        driver = context.driver
        snapshot = context_snapshot(driver)
        system = (
            "You are a demand anticipation agent for a ride-hailing driver app. "
            "Given the driver's current context, suggest ONE zone where demand will likely spike soon, or say not to move. "
            "Reply with JSON only. Use this exact shape: "
            '{"suggest_move": true or false, "target_zone": "e.g. Downtown Dubai or Dubai Marina or Mall of Emirates or JBR or Airport T1", '
            '"mins_until_peak": number (minutes), "title": "short title", "description": "1-2 sentences for the driver", '
            '"reasoning": ["reason1", "reason2"], "confidence": 0.0 to 1.0}. '
            "If suggest_move is false, you may omit target_zone and mins_until_peak. "
            "Use only the zone names listed above for target_zone."
        )
        user = f"Driver context: {snapshot}\n\nOutput one JSON object with your recommendation."
        out = ask_agent(system, user)
        if not out or not out.get("suggest_move"):
            return []
        zone_name = (out.get("target_zone") or "").strip().lower()
        mins = int(out.get("mins_until_peak") or 10)
        coords = None
        for key, (lat, lng, label) in _ZONES.items():
            if key in zone_name or zone_name in key:
                coords = (lat, lng, label)
                break
        if not coords:
            coords = (25.1972, 55.2744, "Downtown Dubai")
        lat, lng, label = coords
        return [
            Recommendation(
                agent_id=self.agent_id,
                type=RecommendationType.MOVE,
                title=out.get("title") or f"Move toward {label}",
                description=out.get("description") or f"Demand will spike near {label} in ~{mins} minutes.",
                confidence=float(out.get("confidence") or 0.75),
                reasoning=out.get("reasoning") or [],
                action_payload={
                    "target": Location(lat=lat, lng=lng, label=label),
                    "mins_until_peak": mins,
                    "expected_demand_boost": None,
                },
            )
        ]

    def _run_rules(self, context: AgentContext) -> list[Recommendation]:
        driver = context.driver
        if driver.is_on_ride:
            return []
        now = driver.current_time
        hour = now.hour + now.minute / 60.0
        is_rush = (7.5 <= hour <= 9) or (11.5 <= hour <= 13) or (17.5 <= hour <= 20.5)
        weather_boost = 1.2 if driver.weather == "rain" else 1.0
        event_boost = 1.15 if driver.events_nearby else 1.0
        best = None
        best_score = 0.0
        for zone, lat, lng, mins_ahead, boost in self._HOTSPOTS:
            time_factor = max(0, 1 - mins_ahead / 45)
            score = time_factor * boost * weather_boost * event_boost
            if is_rush:
                score *= 1.3
            if score > best_score:
                best_score = score
                best = (zone, lat, lng, mins_ahead, boost)
        if not best or best_score < 0.35:
            return []
        zone, lat, lng, mins_ahead, boost = best
        confidence = min(0.95, 0.4 + best_score * 0.4)
        reasoning = [
            f"Demand in {zone} expected to rise in ~{mins_ahead} mins.",
            "Time-of-day and traffic patterns support this.",
        ]
        if driver.weather == "rain":
            reasoning.append("Rain typically increases short-trip demand.")
        if driver.events_nearby:
            reasoning.append("Nearby events often create pickup clusters.")
        return [
            Recommendation(
                agent_id=self.agent_id,
                type=RecommendationType.MOVE,
                title=f"Move toward {zone}",
                description=f"In ~{mins_ahead} minutes demand will spike near {zone}. Moving now can improve your next pickup.",
                confidence=confidence,
                reasoning=reasoning,
                action_payload={
                    "target": Location(lat=lat, lng=lng, label=zone),
                    "mins_until_peak": mins_ahead,
                    "expected_demand_boost": round((boost - 1) * 100),
                },
            )
        ]

    def run(self, context: AgentContext) -> list[Recommendation]:
        if context.driver.is_on_ride:
            return []
        if is_available():
            recs = self._run_with_llm(context)
            if recs:
                return recs
        return self._run_rules(context)
