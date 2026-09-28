"""
Parking & Waiting Safety Agent — legal/safe waiting, avoid fines.
Detects no-parking zones, suggests legal spots, estimates enforcement risk.
"""

from core.context import AgentContext, Location
from core.recommendations import Recommendation, RecommendationType
from .base import BaseAgent


# Mock: zones where we "know" enforcement is strict (e.g. from crowdsourced ticket data)
_STRICT_ZONES = [
    (25.20, 25.22, 55.26, 55.29),   # Downtown
    (25.25, 25.26, 55.36, 55.37),   # Airport
]
# Legal waiting spots: (lat, lng, label)
_SAFE_SPOTS = [
    (25.1190, 55.1990, "Mall parking lot"),
    (25.0780, 55.1280, "JBR service road"),
    (25.1950, 55.2720, "Business Bay parking"),
]


class ParkingSafetyAgent(BaseAgent):
    """Suggests legal waiting spots and warns about enforcement risk."""

    agent_id = "parking_safety"

    def _in_strict_zone(self, lat: float, lng: float) -> bool:
        for lat_lo, lat_hi, lng_lo, lng_hi in _STRICT_ZONES:
            if lat_lo <= lat <= lat_hi and lng_lo <= lng <= lng_hi:
                return True
        return False

    def run(self, context: AgentContext) -> list[Recommendation]:
        driver = context.driver
        if driver.is_on_ride:
            return []

        recs = []
        lat, lng = driver.current_location.lat, driver.current_location.lng

        if self._in_strict_zone(lat, lng):
            recs.append(
                Recommendation(
                    agent_id=self.agent_id,
                    type=RecommendationType.AVOID_ZONE,
                    title="High enforcement area",
                    description="You're in a zone with frequent parking enforcement. Move to a legal waiting spot to avoid fines.",
                    confidence=0.88,
                    reasoning=[
                        "Crowdsourced ticket data shows high activity here.",
                        "Time-based enforcement is often active at this hour.",
                    ],
                    action_payload={"risk": "high"},
                )
            )

        # Suggest nearest safe spot (simplified: first that's "not current")
        for slat, slng, label in _SAFE_SPOTS:
            if abs(slat - lat) > 0.01 or abs(slng - lng) > 0.01:
                recs.append(
                    Recommendation(
                        agent_id=self.agent_id,
                        type=RecommendationType.PARK,
                        title=f"Legal waiting: {label}",
                        description=f"Move to {label} to wait without enforcement risk. ~2–3 min drive.",
                        confidence=0.85,
                        reasoning=[
                            "No recent ticket reports at this spot.",
                            "Common driver waiting area.",
                        ],
                        action_payload={
                            "target": Location(lat=slat, lng=slng, label=label),
                        },
                    )
                )
                break

        return recs
