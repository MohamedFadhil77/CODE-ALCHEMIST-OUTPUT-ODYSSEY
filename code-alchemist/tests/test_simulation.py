"""Basic tests for the simulation engine."""

import pytest
from simulation import new_mission, advance_day, apply_event, get_status, pick_event_for_day


def test_new_mission_moon():
    m = new_mission("Moon", 4, 21, "standard")
    assert m["destination"] == "Moon"
    assert m["crew_size"] == 4
    assert m["duration_days"] == 21
    assert m["status"] == "active"
    assert 0 < m["resources"]["oxygen_pct"] <= 100


def test_new_mission_mars_challenge():
    m = new_mission("Mars", 6, 30, "challenge")
    assert m["destination"] == "Mars"
    assert m["difficulty"] == "challenge"
    assert m["resources"]["oxygen_pct"] < 80


def test_advance_day_reduces_resources():
    m = new_mission("Moon", 3, 14, "standard")
    o0 = m["resources"]["oxygen_pct"]
    m2 = advance_day(m, None)
    assert m2["day"] == 2
    assert m2["resources"]["oxygen_pct"] <= o0


def test_mission_can_succeed():
    m = new_mission("Moon", 2, 7, "easy")
    for _ in range(10):
        if m["status"] != "active":
            break
        m = advance_day(m, "conserve_resources")
    assert m["status"] in ("success", "failed", "active")


def test_apply_event_oxygen_leak():
    m = new_mission("Mars", 4, 21, "standard")
    o0 = m["resources"]["oxygen_pct"]
    m2 = apply_event(m, "oxygen_leak", "seal_and_repair")
    assert "oxygen_leak" in m2["events_triggered"]
    assert m2["resources"]["oxygen_pct"] < o0


def test_get_status_safe():
    m = new_mission("Moon", 3, 14, "easy")
    assert get_status(m) in ("safe", "warning", "critical")


def test_invalid_destination():
    with pytest.raises(ValueError):
        new_mission("Europa", 3, 10, "standard")
