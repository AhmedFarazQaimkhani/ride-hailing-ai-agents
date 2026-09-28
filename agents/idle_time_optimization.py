"""
Idle-Time Optimization Agent — suggests best waiting spot, breaks, micro-movements.
"Wait here for 6 mins — moving now reduces your chances."
Uses LLM when OPENAI_API_KEY is set; otherwise rule-based.
"""

from core.context import AgentContext, Location
from core.recommendations import Recommendation, RecommendationType
from core.llm import ask_agent, context_snapshot, is_available
from .base import BaseAgent


class IdleTimeOptimizationAgent(BaseAgent):
    """Optimizes what to do when driver has no ride (wait vs move). LLM or rules."""

    agent_id = "idle_time_optimization"

    def _run_with_llm(self, context: AgentContext) -> list[Recommendation]:
        driver = context.driver
        snapshot = context_snapshot(driver)
        system = (
            "You are an idle-time optimization agent for a ride-hailing driver. "
            "Given the driver's context, suggest either WAIT (stay put for a few minutes) or a small MOVE (micro-move to a better spot). "
            "Reply with JSON only: "
            '{"action": "wait" or "move", "title": "short title", "description": "1-2 sentences", '
            '"reasoning": ["reason1", "reason2"], "confidence": 0.0 to 1.0, '
            '"suggested_wait_mins": number if action is wait, else omit}.'
        )
        user = f"Driver context: {snapshot}\n\nOutput one JSON object."
        out = ask_agent(system, user)
        if not out:
            return []
        action = (out.get("action") or "wait").strip().lower()
        rec_type = RecommendationType.WAIT if action == "wait" else RecommendationType.MOVE
        if rec_type == RecommendationType.WAIT:
            payload = {"suggested_wait_mins": int(out.get("suggested_wait_mins") or 6)}
        else:
            payload = {
                "target": Location(
                    driver.current_location.lat + 0.0027,
                    driver.current_location.lng,
                    label="Suggested spot 300m N",
                ),
                "move_type": "micro",
            }
        return [
            Recommendation(
                agent_id=self.agent_id,
                type=rec_type,
                title=out.get("title") or ("Wait here 5–7 minutes" if rec_type == RecommendationType.WAIT else "Small shift north (~300 m)"),
                description=out.get("description") or "",
                confidence=float(out.get("confidence") or 0.7),
                reasoning=out.get("reasoning") or [],
                action_payload=payload,
            )
        ]

    def _run_rules(self, context: AgentContext) -> list[Recommendation]:
        driver = context.driver
        if driver.is_on_ride:
            return []
        recs = []
        if driver.traffic_level == "high" and driver.continuous_driving_minutes < 30:
            recs.append(
                Recommendation(
                    agent_id=self.agent_id,
                    type=RecommendationType.WAIT,
                    title="Wait here 5–7 minutes",
                    description="Moving now in this traffic reduces your pickup chances. Stay put; demand often matches nearby drivers first.",
                    confidence=0.72,
                    reasoning=[
                        "Traffic is high — short moves are costly.",
                        "Opportunity cost of moving now > waiting.",
                    ],
                    action_payload={"suggested_wait_mins": 6},
                )
            )
        if driver.traffic_level != "high" and not recs:
            recs.append(
                Recommendation(
                    agent_id=self.agent_id,
                    type=RecommendationType.MOVE,
                    title="Small shift north (~300 m)",
                    description="A short move to the next block improves visibility to riders and reduces wait time by ~2 mins on average.",
                    confidence=0.58,
                    reasoning=[
                        "Idle density is lower 300m north.",
                        "Micro-movements often trigger faster dispatch in this zone.",
                    ],
                    action_payload={
                        "target": Location(
                            driver.current_location.lat + 0.0027,
                            driver.current_location.lng,
                            label="Suggested spot 300m N",
                        ),
                        "move_type": "micro",
                    },
                )
            )
        return recs

    def run(self, context: AgentContext) -> list[Recommendation]:
        if context.driver.is_on_ride:
            return []
        if is_available():
            recs = self._run_with_llm(context)
            if recs:
                return recs
        return self._run_rules(context)
