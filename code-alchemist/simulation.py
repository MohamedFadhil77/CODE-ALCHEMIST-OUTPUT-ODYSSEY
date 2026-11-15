"""
Outpost Odyssey — Simulation Engine
Deterministic resource and event calculations.
All numeric values are educational assumptions unless a NASA source is cited.
"""

from __future__ import annotations
import copy
import uuid
from typing import Any

# ---------------------------------------------------------------------------
# Educational baseline rates (simplified)
# These are NOT official NASA engineering values.
# ---------------------------------------------------------------------------
BASE_RATES = {
    "Moon": {
        "oxygen_drain_per_crew_day": 2.8,      # % of tank per crew-day
        "water_drain_per_crew_day": 2.2,
        "food_drain_per_crew_day": 1.9,
        "energy_base_drain": 3.5,               # % per day base systems
        "energy_life_support": 1.8,             # extra per crew
        "solar_efficiency": 1.0,                # relative
        "radiation_base_risk": 0.15,
    },
    "Mars": {
        "oxygen_drain_per_crew_day": 3.1,
        "water_drain_per_crew_day": 2.5,
        "food_drain_per_crew_day": 2.1,
        "energy_base_drain": 4.0,
        "energy_life_support": 2.0,
        "solar_efficiency": 0.55,               # weaker sunlight
        "radiation_base_risk": 0.25,
    },
}

DIFFICULTY_MOD = {
    "easy": 0.75,
    "standard": 1.0,
    "challenge": 1.35,
}

# Event definitions (educational training scenarios)
EVENTS = {
    "solar_radiation_alert": {
        "id": "solar_radiation_alert",
        "name": "Solar Radiation Alert",
        "description": "A solar particle event is approaching. Radiation levels outside the habitat will rise sharply for 18–36 hours.",
        "destination": ["Moon", "Mars"],
        "min_day": 3,
        "severity": "high",
        "effects": {
            "no_action": {"equipment_pct": -8, "oxygen_pct": -4},
            "shelter": {"energy_pct": -6, "food_pct": -2},
            "continue_work": {"equipment_pct": -18, "oxygen_pct": -9},
        },
    },
    "power_fault": {
        "id": "power_fault",
        "name": "Power System Fault",
        "description": "A fault has been detected in the primary power distribution unit. Non-essential systems may be affected.",
        "destination": ["Moon", "Mars"],
        "min_day": 2,
        "severity": "medium",
        "effects": {
            "no_action": {"energy_pct": -15, "equipment_pct": -5},
            "switch_backup": {"energy_pct": -4},
            "reduce_load": {"energy_pct": -8, "food_pct": -3, "water_pct": -2},
        },
    },
    "oxygen_leak": {
        "id": "oxygen_leak",
        "name": "Cabin Oxygen Leak",
        "description": "Sensors report a slow pressure drop in the crew cabin. A small leak is likely present.",
        "destination": ["Moon", "Mars"],
        "min_day": 1,
        "severity": "high",
        "effects": {
            "no_action": {"oxygen_pct": -22},
            "seal_and_repair": {"oxygen_pct": -6, "energy_pct": -5, "equipment_pct": -3},
            "isolate_module": {"oxygen_pct": -10, "energy_pct": -3},
        },
    },
    "dust_storm": {
        "id": "dust_storm",
        "name": "Regional Dust Storm",
        "description": "A large dust storm is reducing solar array output and may clog external equipment.",
        "destination": ["Mars"],
        "min_day": 4,
        "severity": "high",
        "effects": {
            "no_action": {"energy_pct": -20, "equipment_pct": -10},
            "stow_arrays": {"energy_pct": -12, "food_pct": -4},
            "run_backup": {"energy_pct": -7, "equipment_pct": -4},
        },
    },
    "water_recycler_glitch": {
        "id": "water_recycler_glitch",
        "name": "Water Recycler Glitch",
        "description": "The water recovery system is reporting reduced efficiency. Crew water reserves will be affected if not addressed.",
        "destination": ["Moon", "Mars"],
        "min_day": 2,
        "severity": "medium",
        "effects": {
            "no_action": {"water_pct": -14},
            "manual_override": {"water_pct": -5, "energy_pct": -4, "equipment_pct": -2},
            "switch_to_reserve": {"water_pct": -8, "energy_pct": -2},
        },
    },
    "equipment_wear": {
        "id": "equipment_wear",
        "name": "Accelerated Equipment Wear",
        "description": "Thermal cycling and dust have increased wear on external systems. Maintenance is recommended.",
        "destination": ["Moon", "Mars"],
        "min_day": 5,
        "severity": "low",
        "effects": {
            "no_action": {"equipment_pct": -9},
            "schedule_maintenance": {"equipment_pct": -3, "energy_pct": -5, "food_pct": -1},
            "defer": {"equipment_pct": -7},
        },
    },
}


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def new_mission(
    destination: str,
    crew_size: int,
    duration_days: int,
    difficulty: str = "standard",
) -> dict[str, Any]:
    """Create a fresh mission state."""
    destination = destination.title()
    if destination not in ("Moon", "Mars"):
        raise ValueError("destination must be 'Moon' or 'Mars'")
    crew_size = max(2, min(6, int(crew_size)))
    duration_days = max(7, min(90, int(duration_days)))
    difficulty = difficulty.lower()
    if difficulty not in DIFFICULTY_MOD:
        difficulty = "standard"

    # Starting resources depend on difficulty
    start = {
        "easy": 92.0,
        "standard": 85.0,
        "challenge": 72.0,
    }[difficulty]

    state: dict[str, Any] = {
        "mission_id": str(uuid.uuid4())[:8],
        "destination": destination,
        "crew_size": crew_size,
        "duration_days": duration_days,
        "difficulty": difficulty,
        "day": 1,
        "status": "active",
        "resources": {
            "oxygen_pct": start,
            "water_pct": start - 2,
            "food_pct": start - 1,
            "energy_pct": start + 3,
            "equipment_pct": start,
        },
        "shielding_level": 1 if difficulty != "challenge" else 0,
        "power_backup": difficulty == "easy",
        "food_production": False,
        "history": [],
        "events_triggered": [],
        "score": None,
        "debrief": None,
        "last_event": None,
        "last_action": None,
        "pending_event": None,
    }
    # Record day 0 baseline
    state["history"].append({
        "day": 0,
        "resources": copy.deepcopy(state["resources"]),
        "event": None,
        "action": "Mission start",
        "notes": f"{destination} outpost — crew {crew_size}, {duration_days} days, {difficulty}",
    })
    return state


def _daily_drain(state: dict) -> dict[str, float]:
    """Compute one day's resource drain (educational formulas)."""
    dest = state["destination"]
    rates = BASE_RATES[dest]
    mod = DIFFICULTY_MOD[state["difficulty"]]
    crew = state["crew_size"]

    oxygen = rates["oxygen_drain_per_crew_day"] * crew * mod
    water = rates["water_drain_per_crew_day"] * crew * mod
    food = rates["food_drain_per_crew_day"] * crew * mod

    # Food production reduces food drain
    if state.get("food_production"):
        food *= 0.55
        # costs extra energy and a little water
        water += 0.8 * crew * 0.3

    energy = rates["energy_base_drain"] * mod
    energy += rates["energy_life_support"] * crew * mod
    if state.get("food_production"):
        energy += 2.5 * mod
    if state.get("power_backup"):
        energy *= 0.92  # slightly more efficient with backup systems

    # Shielding costs a little continuous power
    energy += state.get("shielding_level", 0) * 0.6

    # Solar efficiency affects net energy recovery (simplified)
    solar_gain = 4.5 * rates["solar_efficiency"] * (1.1 if state.get("power_backup") else 1.0)
    net_energy = energy - solar_gain

    equipment = 0.4 * mod  # baseline wear
    if state["destination"] == "Mars":
        equipment += 0.3  # dust

    return {
        "oxygen_pct": oxygen,
        "water_pct": water,
        "food_pct": food,
        "energy_pct": max(0.0, net_energy),  # can be negative (net gain)
        "equipment_pct": equipment,
    }


def get_status(state: dict) -> str:
    """Return overall status string."""
    if state["status"] in ("failed", "success", "aborted"):
        return state["status"]
    res = state["resources"]
    vals = [res["oxygen_pct"], res["water_pct"], res["food_pct"], res["energy_pct"], res["equipment_pct"]]
    if any(v <= 0 for v in vals):
        return "failed"
    if any(v < 15 for v in vals):
        return "critical"
    if any(v < 35 for v in vals):
        return "warning"
    return "safe"


def advance_day(state: dict, player_action: str | None = None) -> dict:
    """
    Advance the mission by one day.
    Applies baseline consumption, optional player action, checks thresholds.
    """
    if state["status"] != "active":
        return state

    state = copy.deepcopy(state)
    day = state["day"]
    notes = []

    # Apply player action effects (simple upgrades)
    if player_action:
        state["last_action"] = player_action
        if player_action == "boost_shielding" and state["shielding_level"] < 3:
            state["shielding_level"] += 1
            state["resources"]["energy_pct"] = _clamp(state["resources"]["energy_pct"] - 8)
            state["resources"]["equipment_pct"] = _clamp(state["resources"]["equipment_pct"] - 3)
            notes.append("Shielding upgraded")
        elif player_action == "install_backup" and not state["power_backup"]:
            state["power_backup"] = True
            state["resources"]["energy_pct"] = _clamp(state["resources"]["energy_pct"] - 10)
            state["resources"]["equipment_pct"] = _clamp(state["resources"]["equipment_pct"] - 4)
            notes.append("Backup power installed")
        elif player_action == "start_food_production" and not state["food_production"]:
            state["food_production"] = True
            state["resources"]["water_pct"] = _clamp(state["resources"]["water_pct"] - 6)
            state["resources"]["energy_pct"] = _clamp(state["resources"]["energy_pct"] - 7)
            notes.append("Food production started")
        elif player_action == "emergency_repair":
            state["resources"]["equipment_pct"] = _clamp(state["resources"]["equipment_pct"] + 12)
            state["resources"]["energy_pct"] = _clamp(state["resources"]["energy_pct"] - 5)
            notes.append("Emergency repair performed")
        elif player_action == "conserve_resources":
            # Temporary efficiency — applied as reduced drain this day
            notes.append("Crew on conservation protocol")

    # Daily drain
    drain = _daily_drain(state)
    if player_action == "conserve_resources":
        for k in drain:
            drain[k] *= 0.7

    for key, amount in drain.items():
        if amount >= 0:
            state["resources"][key] = _clamp(state["resources"][key] - amount)
        else:
            # net gain (energy)
            state["resources"][key] = _clamp(state["resources"][key] - amount)

    # Check failure
    status = get_status(state)
    if status == "failed":
        state["status"] = "failed"
        notes.append("Critical resource depleted — mission failed")

    # Advance day
    state["day"] = day + 1
    if state["day"] > state["duration_days"] and state["status"] == "active":
        state["status"] = "success"
        notes.append("Mission duration completed successfully")

    state["history"].append({
        "day": state["day"] - 1,
        "resources": copy.deepcopy(state["resources"]),
        "event": state.get("last_event"),
        "action": player_action,
        "notes": "; ".join(notes) if notes else "Nominal day",
    })
    state["last_event"] = None
    return state


def apply_event(state: dict, event_id: str, response: str | None = None) -> dict:
    """
    Apply an event and the player's chosen response.
    response should match one of the keys in the event's effects dict.
    """
    if state["status"] != "active":
        return state

    state = copy.deepcopy(state)
    event = EVENTS.get(event_id)
    if not event:
        return state

    if event_id in state["events_triggered"]:
        return state  # already handled

    effects = event["effects"]
    chosen = response if response in effects else "no_action"
    deltas = effects[chosen]

    for key, delta in deltas.items():
        if key in state["resources"]:
            state["resources"][key] = _clamp(state["resources"][key] + delta)

    state["events_triggered"].append(event_id)
    state["last_event"] = event_id
    state["last_action"] = chosen
    state["pending_event"] = None

    # Immediate failure check
    if get_status(state) == "failed":
        state["status"] = "failed"

    state["history"].append({
        "day": state["day"],
        "resources": copy.deepcopy(state["resources"]),
        "event": event_id,
        "action": chosen,
        "notes": f"Event '{event['name']}' — response: {chosen}",
    })
    return state


def pick_event_for_day(state: dict) -> str | None:
    """
    Deterministically decide whether an event occurs on the current day.
    Returns event_id or None.
    """
    import hashlib
    day = state["day"]
    dest = state["destination"]
    difficulty = state["difficulty"]
    seed = f"{state['mission_id']}-{day}-{dest}"
    h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)

    # Probability roughly scales with difficulty
    chance = {"easy": 0.22, "standard": 0.38, "challenge": 0.55}[difficulty]
    if (h % 100) / 100.0 > chance:
        return None

    candidates = [
        eid for eid, e in EVENTS.items()
        if dest in e["destination"]
        and day >= e["min_day"]
        and eid not in state["events_triggered"]
    ]
    if not candidates:
        return None
    return candidates[h % len(candidates)]


def get_event_info(event_id: str) -> dict | None:
    return EVENTS.get(event_id)


def list_possible_actions() -> list[dict]:
    """Actions the player can take on a normal day."""
    return [
        {"id": "none", "label": "Continue nominal operations"},
        {"id": "conserve_resources", "label": "Conserve resources (reduce drain)"},
        {"id": "boost_shielding", "label": "Upgrade radiation shielding"},
        {"id": "install_backup", "label": "Install / reinforce backup power"},
        {"id": "start_food_production", "label": "Start / expand food production"},
        {"id": "emergency_repair", "label": "Emergency equipment repair"},
    ]
