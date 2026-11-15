"""
Outpost Odyssey — Educational mission scenarios and event catalogue.
Scenarios are training situations, not real-time operational advice.
"""

from __future__ import annotations
from simulation import EVENTS, get_event_info


def get_available_events(destination: str, day: int, difficulty: str) -> list[dict]:
    """Return events that could fire for this destination/day."""
    dest = destination.title()
    out = []
    for eid, e in EVENTS.items():
        if dest in e["destination"] and day >= e["min_day"]:
            out.append({
                "id": e["id"],
                "name": e["name"],
                "description": e["description"],
                "severity": e["severity"],
                "responses": list(e["effects"].keys()),
            })
    return out


def get_event_by_id(event_id: str) -> dict | None:
    e = get_event_info(event_id)
    if not e:
        return None
    return {
        "id": e["id"],
        "name": e["name"],
        "description": e["description"],
        "severity": e["severity"],
        "responses": list(e["effects"].keys()),
        "effects_summary": {k: v for k, v in e["effects"].items()},
    }


def get_demo_story() -> dict:
    """Suggested demo path for presentation."""
    return {
        "title": "Mars 21-day Challenge Run",
        "steps": [
            "Select Mars, crew of 4, 21 days, standard difficulty.",
            "On day 1–3 run nominal operations and start food production when energy allows.",
            "When a solar radiation or power fault appears, choose the protective response.",
            "Finish the mission and open the debrief report.",
            "Ask the AI Mission Coach why a particular resource became the bottleneck.",
        ],
        "learning_goal": "Feel the trade-off between radiation protection, power and food production under limited mass and energy.",
    }
