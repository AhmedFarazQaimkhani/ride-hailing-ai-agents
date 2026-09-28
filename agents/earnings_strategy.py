"""
Earnings Strategy Agent — personalized: when to log in/out, which rides to accept.
"Skipping this ride likely gives higher fare in 8 mins nearby."
Uses LLM when OPENAI_API_KEY is set; otherwise rule-based.
"""

from core.context import AgentContext
from core.recommendations import Recommendation, RecommendationType
from core.llm import ask_agent, context_snapshot, is_available
from .base import BaseAgent


class EarningsStrategyAgent(BaseAgent):
    """Suggests log-in timing and accept/skip. LLM or rules."""

    agent_id = "earnings_strategy"

    def _run_with_llm(self, context: AgentContext) -> list[Recommendation]:
        driver = context.driver
        snapshot = context_snapshot(driver)
        offer = context.extra.get("current_offer")
        offer_text = f"Current ride offer: fare {offer.get('fare')}, eta {offer.get('eta_mins')} min." if offer else "No current offer."
        system = (
            "You are an earnings strategy agent for a ride-hailing driver. "
            "Suggest at most ONE actionable tip: either (1) log in soon (if approaching preferred hours), or (2) accept/skip the current ride offer. "
            "Reply with JSON only: "
            '{"suggest": true or false, "type": "info" or "skip_ride" or "accept_ride", '
            '"title": "short title", "description": "1-2 sentences", "reasoning": ["r1","r2"], "confidence": 0.0 to 1.0}. '
            "If suggest is false, omit the rest. Use skip_ride only if there is an offer and skipping might yield better fare; use info for log-in timing."
        )
        user = f"Driver context: {snapshot}\n{offer_text}\n\nOutput one JSON object."
        out = ask_agent(system, user)
        if not out or not out.get("suggest"):
            return []
        t = (out.get("type") or "info").strip().lower()
        type_map = {"skip_ride": RecommendationType.SKIP_RIDE, "accept_ride": RecommendationType.ACCEPT_RIDE, "info": RecommendationType.INFO}
        rec_type = type_map.get(t, RecommendationType.INFO)
        payload = {}
        if offer and rec_type == RecommendationType.SKIP_RIDE:
            payload = {"expected_wait_mins": 8, "current_fare": offer.get("fare")}
        elif rec_type == RecommendationType.INFO:
            payload = {"suggested_log_in": True}
        return [
            Recommendation(
                agent_id=self.agent_id,
                type=rec_type,
                title=out.get("title") or "",
                description=out.get("description") or "",
                confidence=float(out.get("confidence") or 0.7),
                reasoning=out.get("reasoning") or [],
                action_payload=payload,
            )
        ]

    def _run_rules(self, context: AgentContext) -> list[Recommendation]:
        driver = context.driver
        recs = []
        now = driver.current_time
        hour = now.hour
        start, end = driver.preferred_hours
        if hour < start and start - hour <= 2:
            recs.append(
                Recommendation(
                    agent_id=self.agent_id,
                    type=RecommendationType.INFO,
                    title="Peak window starting soon",
                    description=f"Your preferred window ({start}:00–{end}:00) starts in {start - hour} hour(s). Logging in now can capture early surge.",
                    confidence=0.78,
                    reasoning=[
                        "Historical earnings are higher when you start at window open.",
                        "Surge often builds in the first 30 mins.",
                    ],
                    action_payload={"suggested_log_in": True},
                )
            )
        offer = context.extra.get("current_offer")
        if not driver.is_on_ride and offer:
            fare = offer.get("fare", 0)
            if fare < 25 and driver.risk_tolerance in ("medium", "high"):
                recs.append(
                    Recommendation(
                        agent_id=self.agent_id,
                        type=RecommendationType.SKIP_RIDE,
                        title="Consider skipping this ride",
                        description=f"Skipping this ride (fare ~{fare}) likely yields a higher fare in ~8 mins nearby. Best if you're comfortable waiting.",
                        confidence=0.65,
                        reasoning=[
                            "Nearby demand is trending up.",
                            "Your acceptance behavior suggests you optimize for fare size.",
                        ],
                        action_payload={"expected_wait_mins": 8, "current_fare": fare},
                    )
                )
        return recs

    def run(self, context: AgentContext) -> list[Recommendation]:
        if is_available():
            recs = self._run_with_llm(context)
            if recs:
                return recs
        return self._run_rules(context)
