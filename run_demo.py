#!/usr/bin/env python3
"""
Demo: Run the Driver Co-Pilot with mock context and print recommendations.
Usage: python run_demo.py [scenario]
Scenarios: default | fatigue | multi_app | rain_event

Loads .env so OPENAI_API_KEY is used by the Explainable Coach when set (optional).
"""

import sys
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.context import AgentContext
from copilot import DriverCoPilot
from data.mock_context import make_demo_context

console = Console()


def scenario_default() -> AgentContext:
    """Idle driver, clear weather, normal traffic."""
    driver = make_demo_context(
        is_on_ride=False,
        current_app="uber",
        continuous_driving_minutes=45.0,
        weather="clear",
        traffic_level="normal",
    )
    return AgentContext(driver=driver)


def scenario_fatigue() -> AgentContext:
    """Long session without break — should trigger fatigue agent."""
    driver = make_demo_context(
        is_on_ride=False,
        current_app="careem",
        continuous_driving_minutes=220.0,
        weather="clear",
        traffic_level="normal",
    )
    return AgentContext(driver=driver)


def scenario_multi_app() -> AgentContext:
    """Driver on multiple apps, evening rush — multi-app arbitrage."""
    driver = make_demo_context(
        is_on_ride=False,
        current_app="uber",
        continuous_driving_minutes=30.0,
        weather="clear",
        traffic_level="high",
        current_hour=18,
    )
    return AgentContext(driver=driver)


def scenario_rain_event() -> AgentContext:
    """Rain + event — demand anticipation and parking matter."""
    driver = make_demo_context(
        is_on_ride=False,
        current_app="uber",
        continuous_driving_minutes=20.0,
        weather="rain",
        traffic_level="high",
        events_nearby=["concert_at_arena"],
        current_hour=19,
    )
    driver.current_location.label = "Near Downtown"
    return AgentContext(driver=driver)


SCENARIOS = {
    "default": ("Idle driver, clear weather", scenario_default),
    "fatigue": ("Long session, no break", scenario_fatigue),
    "multi_app": ("Evening rush, multi-app", scenario_multi_app),
    "rain_event": ("Rain + event nearby", scenario_rain_event),
}


def run(scenario_name: str = "default") -> None:
    scenarios = SCENARIOS
    if scenario_name not in scenarios:
        console.print(f"Unknown scenario: [red]{scenario_name}[/red]. Choose from: {list(scenarios)}")
        return
    title, get_context = scenarios[scenario_name]
    context = get_context()

    copilot = DriverCoPilot()
    recs = copilot.recommend(context)

    console.print(Panel(f"[bold]Driver Co-Pilot[/bold] — {title}", style="blue"))
    console.print(f"Time: {context.driver.current_time.strftime('%H:%M')} | "
                  f"On ride: {context.driver.is_on_ride} | "
                  f"App: {context.driver.current_app or 'idle'} | "
                  f"Driving: {context.driver.continuous_driving_minutes:.0f} min")
    console.print()

    if not recs:
        console.print("[dim]No recommendations above confidence threshold.[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Agent", style="dim", width=22)
    table.add_column("Type", width=12)
    table.add_column("Recommendation", width=48)
    table.add_column("Confidence", width=8)
    table.add_column("Explanation", width=56)

    for r in recs:
        table.add_row(
            r.agent_id,
            r.type.value,
            f"[bold]{r.title}[/bold]\n{r.description}",
            f"{r.confidence:.0%}",
            r.explanation or "—",
        )
    console.print(table)


if __name__ == "__main__":
    scenario = sys.argv[1] if len(sys.argv) > 1 else "default"
    run(scenario)
