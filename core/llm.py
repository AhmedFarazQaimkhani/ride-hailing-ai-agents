"""
Shared LLM client for ride-hailing agents.
When OPENAI_API_KEY is set, agents can call OpenAI to generate recommendations.
"""

import json
import os
from typing import Any, Optional


def is_available() -> bool:
    """True if OpenAI API key is set and we can call the API."""
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def _client():
    """Lazy OpenAI client (only when key is set)."""
    from openai import OpenAI
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def ask_agent(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str = "gpt-4o-mini",
    json_mode: bool = True,
    max_tokens: int = 500,
) -> Optional[dict[str, Any]]:
    """
    Call OpenAI and return the assistant message as a dict (if json_mode) or raw text.
    Returns None if no key, on API error, or if parsing fails.
    """
    if not is_available():
        return None
    try:
        client = _client()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        kwargs = {"model": model, "messages": messages, "max_tokens": max_tokens}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        r = client.chat.completions.create(**kwargs)
        if not r.choices or not r.choices[0].message.content:
            return None
        text = r.choices[0].message.content.strip()
        if json_mode:
            return json.loads(text)
        return {"text": text}
    except Exception:
        return None


def context_snapshot(driver) -> str:
    """Build a short text snapshot of driver context for LLM prompts."""
    loc = driver.current_location
    return (
        f"Time: {driver.current_time.strftime('%H:%M')} ({driver.current_time.strftime('%A')}). "
        f"Location: {loc.label or 'current'} (lat {loc.lat}, lng {loc.lng}). "
        f"Weather: {driver.weather}. Traffic: {driver.traffic_level}. "
        f"On ride: {driver.is_on_ride}. Current app: {driver.current_app or 'idle'}. "
        f"Driving continuously: {driver.continuous_driving_minutes:.0f} min. "
        f"Rides today: {driver.total_rides_today}. "
        f"Preferred hours: {driver.preferred_hours[0]}:00–{driver.preferred_hours[1]}:00. "
        f"Risk tolerance: {driver.risk_tolerance}. "
        f"Events nearby: {driver.events_nearby or 'none'}. "
        f"Apps enabled: {', '.join(driver.apps_enabled)}."
    )
