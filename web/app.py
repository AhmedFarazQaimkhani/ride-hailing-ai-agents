"""
Web API for Driver Co-Pilot — serves context + recommendations for the UI.
"""

import sys
from pathlib import Path

# Project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from core.context import AgentContext, Location
from core.recommendations import Recommendation
from copilot import DriverCoPilot
from data.mock_context import make_demo_context

app = FastAPI(title="Driver Co-Pilot", version="1.0")

SCENARIOS = {
    "default": {
        "label": "Idle driver, clear weather",
        "kwargs": dict(is_on_ride=False, current_app="uber", continuous_driving_minutes=45.0, weather="clear", traffic_level="normal"),
    },
    "fatigue": {
        "label": "Long session, no break",
        "kwargs": dict(is_on_ride=False, current_app="careem", continuous_driving_minutes=220.0, weather="clear", traffic_level="normal"),
    },
    "multi_app": {
        "label": "Evening rush, multi-app",
        "kwargs": dict(is_on_ride=False, current_app="uber", continuous_driving_minutes=30.0, weather="clear", traffic_level="high", current_hour=18),
    },
    "rain_event": {
        "label": "Rain + event nearby",
        "kwargs": dict(is_on_ride=False, current_app="uber", continuous_driving_minutes=20.0, weather="rain", traffic_level="high", events_nearby=["concert_at_arena"], current_hour=19),
    },
    "morning": {
        "label": "Early morning — log in soon",
        "kwargs": dict(is_on_ride=False, current_app=None, continuous_driving_minutes=0, weather="clear", traffic_level="normal", current_hour=7),
    },
    "skip_ride": {
        "label": "Low fare offer — skip?",
        "kwargs": dict(is_on_ride=False, current_app="uber", continuous_driving_minutes=25.0, weather="clear", traffic_level="normal"),
        "extra": {"current_offer": {"fare": 18, "eta_mins": 5}},
    },
    "parking_risk": {
        "label": "Waiting in high-enforcement zone",
        "kwargs": dict(is_on_ride=False, current_app="uber", continuous_driving_minutes=15.0, weather="clear", traffic_level="normal"),
        "location_override": (25.21, 55.275, "Downtown Dubai"),
    },
}


def _serialize_location(obj):
    if isinstance(obj, Location):
        return {"lat": obj.lat, "lng": obj.lng, "label": obj.label}
    return obj


def _recommendation_to_dict(r: Recommendation) -> dict:
    payload = {}
    for k, v in r.action_payload.items():
        payload[k] = _serialize_location(v)
    return {
        "agent_id": r.agent_id,
        "type": r.type.value,
        "title": r.title,
        "description": r.description,
        "confidence": round(r.confidence, 2),
        "reasoning": r.reasoning or [],
        "action_payload": payload,
        "explanation": r.explanation or "",
    }


@app.get("/api/scenarios")
def list_scenarios():
    return {"scenarios": [{"id": k, "label": v["label"]} for k, v in SCENARIOS.items()]}


@app.get("/api/recommend")
def recommend(scenario: str = "default"):
    if scenario not in SCENARIOS:
        scenario = "default"
    info = SCENARIOS[scenario]
    kwargs = dict(info["kwargs"])
    if "location_override" in info:
        lat, lng, label = info["location_override"]
        kwargs["current_location"] = Location(lat, lng, label)
    driver = make_demo_context(**kwargs)
    context = AgentContext(driver=driver, extra=info.get("extra", {}))
    copilot = DriverCoPilot()
    recs = copilot.recommend(context)
    ctx = context.driver
    loc = ctx.current_location
    return {
        "scenario": scenario,
        "scenario_label": info["label"],
        "context": {
            "time": ctx.current_time.isoformat(),
            "time_short": ctx.current_time.strftime("%H:%M"),
            "date_short": ctx.current_time.strftime("%a, %b %d"),
            "on_ride": ctx.is_on_ride,
            "current_app": ctx.current_app or "idle",
            "driving_mins": round(ctx.continuous_driving_minutes),
            "rides_today": ctx.total_rides_today,
            "weather": ctx.weather,
            "traffic_level": ctx.traffic_level,
            "location_label": loc.label or "Current position",
            "apps_enabled": ctx.apps_enabled,
        },
        "recommendations": [_recommendation_to_dict(r) for r in recs],
    }


# Serve static UI
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index():
        return (static_dir / "index.html").read_text(encoding="utf-8")
