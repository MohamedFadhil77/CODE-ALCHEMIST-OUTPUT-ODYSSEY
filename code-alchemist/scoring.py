"""
Outpost Odyssey — Mission Scoring
Educational scoring that rewards survival, resource management and good decisions.
"""

from __future__ import annotations
from typing import Any


def calculate_mission_score(state: dict, history: list | None = None) -> dict[str, Any]:
    """
    Compute a final score and learning-oriented breakdown.
    Returns dict with score (0-100), grade, breakdown and lessons.
    """
    history = history or state.get("history", [])
    res = state.get("resources", {})
    status = state.get("status", "active")
    difficulty = state.get("difficulty", "standard")
    duration = state.get("duration_days", 30)
    day = state.get("day", 1)
    events = state.get("events_triggered", [])

    breakdown = {
        "survival": 0.0,
        "resources": 0.0,
        "equipment": 0.0,
        "events_handled": 0.0,
        "efficiency": 0.0,
        "difficulty_bonus": 0.0,
    }
    lessons: list[str] = []

    # 1. Survival (max 30)
    if status == "success":
        breakdown["survival"] = 30.0
        lessons.append("You kept the crew alive for the full planned duration.")
    elif status == "failed":
        progress = min(1.0, (day - 1) / max(1, duration))
        breakdown["survival"] = round(12.0 * progress, 1)
        lessons.append("The mission ended early because a critical resource reached zero. Next time prioritise the bottleneck resource.")
    else:
        # still active — partial credit
        progress = min(1.0, (day - 1) / max(1, duration))
        breakdown["survival"] = round(20.0 * progress, 1)

    # 2. Remaining resources (max 25)
    avg_res = (
        res.get("oxygen_pct", 0)
        + res.get("water_pct", 0)
        + res.get("food_pct", 0)
        + res.get("energy_pct", 0)
    ) / 4.0
    breakdown["resources"] = round(min(25.0, avg_res * 0.28), 1)
    if avg_res < 25:
        lessons.append("Average remaining resources are low. Consider earlier conservation or investing in food production / recycling.")
    elif avg_res > 55:
        lessons.append("Strong resource reserve at the end — good planning of daily consumption versus capacity.")

    # 3. Equipment (max 15)
    eq = res.get("equipment_pct", 0)
    breakdown["equipment"] = round(min(15.0, eq * 0.15), 1)
    if eq < 30:
        lessons.append("Equipment condition is poor. Schedule maintenance before systems degrade further.")

    # 4. Events handled (max 15)
    # Simple heuristic: more events survived = better, but only if mission didn't fail immediately after
    n_events = len(events)
    if n_events == 0:
        breakdown["events_handled"] = 5.0
        lessons.append("No major training events occurred. Try a higher difficulty for more decision practice.")
    else:
        breakdown["events_handled"] = min(15.0, 4.0 + n_events * 3.5)
        if status != "failed":
            lessons.append(f"You successfully responded to {n_events} training event(s). Review which response conserved the most critical resource.")
        else:
            lessons.append("An event contributed to mission failure. Re-examine the trade-offs you chose during that alert.")

    # 5. Efficiency / decision quality (max 10)
    # Reward having invested in systems
    systems = 0
    if state.get("shielding_level", 0) >= 2:
        systems += 1
    if state.get("power_backup"):
        systems += 1
    if state.get("food_production"):
        systems += 1
    breakdown["efficiency"] = min(10.0, systems * 3.5)
    if systems == 0:
        lessons.append("You did not invest in extra systems (shielding, backup power or food production). These create resilience against events.")

    # 6. Difficulty bonus (max 5)
    diff_bonus = {"easy": 0.0, "standard": 2.5, "challenge": 5.0}
    breakdown["difficulty_bonus"] = diff_bonus.get(difficulty, 0.0)

    total = sum(breakdown.values())
    total = round(min(100.0, max(0.0, total)), 1)

    if total >= 85:
        grade = "A — Outstanding command"
    elif total >= 70:
        grade = "B — Solid mission"
    elif total >= 55:
        grade = "C — Survived with lessons"
    elif total >= 40:
        grade = "D — Difficult mission"
    else:
        grade = "F — Critical failure"

    if not lessons:
        lessons.append("Review the daily history to see which days caused the largest resource drops.")

    return {
        "score": total,
        "grade": grade,
        "breakdown": breakdown,
        "lessons": lessons[:5],
        "status": status,
        "days_survived": max(0, day - 1),
        "events_count": n_events,
    }
