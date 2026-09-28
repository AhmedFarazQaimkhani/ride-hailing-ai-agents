"""Driver and agent context models — inputs for all agents."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Location:
    """Lat/lng and optional label."""
    lat: float
    lng: float
    label: Optional[str] = None


@dataclass
class DriverContext:
    """Current state of the driver and environment — shared by all agents."""

    # Identity & preferences
    driver_id: str
    preferred_hours: tuple[int, int]  # (start_hour, end_hour) e.g. (9, 21)
    risk_tolerance: str  # "low" | "medium" | "high"
    areas_familiar: list[str]  # zone names

    # Current state
    current_location: Location
    is_on_ride: bool
    current_app: Optional[str] = None  # "uber" | "careem" | "indrive" | None if idle
    apps_enabled: list[str] = field(default_factory=lambda: ["uber", "careem"])

    # Time & fatigue
    session_start: datetime = field(default_factory=datetime.now)
    last_break_at: Optional[datetime] = None
    continuous_driving_minutes: float = 0.0
    total_rides_today: int = 0

    # Environment (can be enriched by external APIs)
    current_time: datetime = field(default_factory=datetime.now)
    weather: str = "clear"  # "clear" | "rain" | "storm"
    traffic_level: str = "normal"  # "low" | "normal" | "high"
    events_nearby: list[str] = field(default_factory=list)  # e.g. ["concert_at_arena"]


@dataclass
class AgentContext:
    """Enriched context passed to agents (driver + optional extra)."""

    driver: DriverContext
    # Optional: historical demand snapshot, map tiles, etc.
    extra: dict = field(default_factory=dict)
