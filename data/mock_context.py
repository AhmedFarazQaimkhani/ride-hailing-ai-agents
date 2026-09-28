"""Build mock DriverContext for demos."""

from datetime import datetime, timedelta

from core.context import DriverContext, Location


def make_demo_context(
    *,
    is_on_ride: bool = False,
    current_app: str | None = "uber",
    continuous_driving_minutes: float = 0.0,
    weather: str = "clear",
    traffic_level: str = "normal",
    events_nearby: list[str] | None = None,
    current_hour: int | None = None,
    current_location: Location | None = None,
) -> DriverContext:
    """Create a driver context for testing/demo."""
    now = datetime.now()
    if current_hour is not None:
        now = now.replace(hour=current_hour, minute=30, second=0, microsecond=0)
    session_start = now - timedelta(minutes=continuous_driving_minutes)
    location = current_location or Location(25.12, 55.19, label="Current position")

    return DriverContext(
        driver_id="demo_driver_1",
        preferred_hours=(9, 21),
        risk_tolerance="medium",
        areas_familiar=["Dubai Marina", "Downtown", "JBR"],
        current_location=location,
        is_on_ride=is_on_ride,
        current_app=current_app,
        apps_enabled=["uber", "careem", "indrive"],
        session_start=session_start,
        last_break_at=session_start - timedelta(hours=1) if continuous_driving_minutes > 60 else None,
        continuous_driving_minutes=continuous_driving_minutes,
        total_rides_today=12,
        current_time=now,
        weather=weather,
        traffic_level=traffic_level,
        events_nearby=events_nearby or [],
    )
