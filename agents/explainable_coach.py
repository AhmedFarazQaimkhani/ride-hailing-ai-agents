"""
Explainable AI Coach — wraps agent outputs with clear reasoning.
Builds trust: "I suggested this zone because: 3 drivers left, event ends in 10 mins, avg fare ↑ 18%."

AI usage:
- Without OPENAI_API_KEY: uses rule-based explanations (no API calls).
- With OPENAI_API_KEY: optionally calls OpenAI to generate a short, natural-language explanation.
"""

import os
from core.context import AgentContext
from core.recommendations import Recommendation, RecommendationType
from .base import BaseAgent


def _explain_with_llm(recommendation: Recommendation) -> str | None:
    """If OPENAI_API_KEY is set, call OpenAI to generate one short sentence. Else return None."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        prompt = (
            "You are a ride-hailing driver co-pilot. In one short sentence (under 25 words), "
            "explain to the driver why we suggest this, in a friendly way. "
            f"Recommendation type: {recommendation.type.value}. "
            f"Title: {recommendation.title}. "
            f"Reasons: {recommendation.reasoning!r}."
        )
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
        )
        if r.choices and r.choices[0].message.content:
            return r.choices[0].message.content.strip()
    except Exception:
        pass
    return None


def _explain_with_rules(recommendation: Recommendation) -> str:
    """Rule-based fallback when no LLM is used."""
    parts = list(recommendation.reasoning) if recommendation.reasoning else []
    if recommendation.type == RecommendationType.MOVE and "target" in recommendation.action_payload:
        t = recommendation.action_payload["target"]
        label = getattr(t, "label", None) or "this area"
        parts.append(f"I suggested {label} because demand is expected to rise there soon.")
    elif recommendation.type == RecommendationType.WAIT:
        parts.append("Waiting here is better than moving right now given current traffic and demand.")
    elif recommendation.type == RecommendationType.BREAK:
        parts.append("Taking a short break now will help you earn better in the next hours.")
    elif recommendation.type in (RecommendationType.PARK, RecommendationType.AVOID_ZONE):
        parts.append("This helps you avoid parking fines and stay safe while waiting.")
    return " • ".join(parts)


class ExplainableCoachAgent(BaseAgent):
    """
    Post-processes recommendations from other agents and adds/enhances explanations.
    Does not produce its own recommendations; it enriches others'.
    Uses OpenAI for explanations only when OPENAI_API_KEY is set.
    """

    agent_id = "explainable_coach"

    def run(self, context: AgentContext) -> list[Recommendation]:
        # This agent is typically used by the orchestrator to enrich recs from other agents.
        return []

    @staticmethod
    def enrich(recommendation: Recommendation) -> Recommendation:
        """Add a short, human-readable explanation. Uses LLM if OPENAI_API_KEY is set, else rules."""
        if recommendation.explanation and len(recommendation.explanation) > 50:
            return recommendation

        explanation = _explain_with_llm(recommendation)
        if explanation is None:
            explanation = _explain_with_rules(recommendation)

        recommendation.explanation = explanation
        return recommendation
