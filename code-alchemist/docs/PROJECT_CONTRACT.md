# PROJECT CONTRACT — Outpost Odyssey
**CODE ALCHEMIST | NASA Space Apps Challenge 2026**

This document is the single source of truth for shared interfaces.
All modules must follow these exact function signatures and data shapes.

---

## 1. Mission State (dict)

```python
{
    "mission_id": str,
    "destination": "Moon" | "Mars",
    "crew_size": int,                 # 2–6
    "duration_days": int,             # 7–90
    "difficulty": "easy" | "standard" | "challenge",
    "day": int,                       # current day (1-based)
    "status": "active" | "success" | "failed" | "aborted",
    "resources": {
        "oxygen_pct": float,          # 0–100
        "water_pct": float,
        "food_pct": float,
        "energy_pct": float,
        "equipment_pct": float
    },
    "shielding_level": int,           # 0–3
    "power_backup": bool,
    "food_production": bool,
    "history": [                      # list of daily snapshots
        {
            "day": int,
            "resources": {...},
            "event": str | None,
            "action": str | None,
            "notes": str
        }
    ],
    "events_triggered": [str],
    "score": float | None,
    "debrief": dict | None
}
```

---

## 2. Core Interfaces

### simulation.py
```python
def new_mission(destination: str, crew_size: int, duration_days: int, difficulty: str) -> dict
def advance_day(state: dict, player_action: str | None = None) -> dict
def apply_event(state: dict, event_id: str, response: str | None = None) -> dict
def get_status(state: dict) -> str   # "safe" | "warning" | "critical" | "failed"
```

### scoring.py
```python
def calculate_mission_score(state: dict, history: list) -> dict
# returns {"score": float, "grade": str, "breakdown": dict, "lessons": list[str]}
```

### ai_advisor.py
```python
def get_advice(state: dict, question: str, approved_facts: list[dict] | None = None) -> dict
# returns {"summary": str, "options": list[dict], "sources": list[str], "uncertainty": str, "fallback": bool}
```

### nasa_data.py
```python
def get_source_catalog() -> list[dict]
def get_event_context(event_id: str) -> dict
def get_destination_facts(destination: str) -> list[dict]
```

### scenarios.py
```python
def get_available_events(destination: str, day: int, difficulty: str) -> list[dict]
def get_event_by_id(event_id: str) -> dict | None
```

---

## 3. Resource rates (educational assumptions)

All rates are labelled as simplified educational parameters unless a NASA source is cited.

- Oxygen: ~0.84 kg O2 per person per day (simplified to % drain)
- Water: ~3.5 L per person per day (hygiene + drinking, recycling assumed)
- Food: ~1.8 kg per person per day
- Energy: base load + life support + production systems

Exact % formulas live in simulation.py and are documented in the app’s “Simulation assumptions” panel.

---

## 4. Rules

1. Simulation engine owns all numeric changes. AI never modifies state.
2. Every external fact must appear in `data/source_catalog.csv` with title, URL, access date, use and limits.
3. If Gemini is unavailable, return a deterministic rule-based hint.
4. Keep `.env` out of git. Use `.env.example` only.
5. One complete playable mission loop is more important than unfinished advanced features.
