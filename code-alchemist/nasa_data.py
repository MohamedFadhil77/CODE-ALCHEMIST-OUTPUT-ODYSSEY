"""
Outpost Odyssey — NASA data and provenance module.
All facts are educational. Simulation rates remain labelled assumptions.
"""

from __future__ import annotations
import csv
import os
from pathlib import Path
from typing import Any

import requests

DATA_DIR = Path(__file__).parent / "data"
CATALOG_PATH = DATA_DIR / "source_catalog.csv"

# Fallback facts used when network is unavailable
FALLBACK_FACTS = {
    "Moon": [
        {
            "title": "Artemis Program Overview",
            "summary": "NASA's Artemis program aims to return humans to the Moon and establish a sustainable presence, testing technologies needed for Mars.",
            "url": "https://www.nasa.gov/specials/artemis/",
            "use": "Mission context and destination motivation",
        },
        {
            "title": "Lunar Environment — Radiation",
            "summary": "The Moon has no global magnetic field and only a tenuous exosphere, so crews are exposed to galactic cosmic rays and solar particle events.",
            "url": "https://www.nasa.gov/moon/",
            "use": "Radiation-alert scenario context",
        },
        {
            "title": "Lunar Dust Challenges",
            "summary": "Lunar regolith is abrasive and electrostatically charged; it can interfere with seals, radiators and mechanisms.",
            "url": "https://www.nasa.gov/moon/",
            "use": "Equipment-wear educational context",
        },
    ],
    "Mars": [
        {
            "title": "Mars Exploration Overview",
            "summary": "Mars has a thin CO2 atmosphere, large dust storms, and higher radiation than Earth. Future human missions will need robust life support and power systems.",
            "url": "https://mars.nasa.gov/",
            "use": "Destination environment context",
        },
        {
            "title": "Martian Dust Storms",
            "summary": "Regional and global dust storms can last weeks and significantly reduce solar-array output, a key design driver for surface power systems.",
            "url": "https://mars.nasa.gov/",
            "use": "Dust-storm training scenario",
        },
        {
            "title": "Mars Radiation Environment",
            "summary": "Surface radiation on Mars is higher than on Earth; habitat shielding and operational constraints during solar events are important for crew safety.",
            "url": "https://mars.nasa.gov/",
            "use": "Radiation-alert scenario context",
        },
    ],
}

EVENT_CONTEXT = {
    "solar_radiation_alert": {
        "title": "Solar Particle Events (educational)",
        "summary": "Solar particle events can increase radiation dose rates for crews outside Earth's magnetosphere. Training scenarios use historical space-weather concepts from NASA DONKI and related education material.",
        "url": "https://ccmc.gsfc.nasa.gov/donki/",
        "limitation": "This game does not compute real radiation doses. Values are simplified for learning.",
    },
    "dust_storm": {
        "title": "Mars Dust Storms",
        "summary": "Dust storms can reduce insolation and affect solar power. NASA Mars missions have observed regional and planet-encircling storms.",
        "url": "https://mars.nasa.gov/",
        "limitation": "Game effects are educational approximations, not engineering predictions.",
    },
    "power_fault": {
        "title": "Surface Power Systems",
        "summary": "Reliable power is essential for life support, communications and science. Redundancy and load management are standard engineering practices.",
        "url": "https://www.nasa.gov/",
        "limitation": "Fault effects in the game are simplified training events.",
    },
    "oxygen_leak": {
        "title": "Cabin Atmosphere Management",
        "summary": "Closed-loop life support must detect and respond to pressure anomalies. Training emphasises rapid isolation and repair decisions.",
        "url": "https://www.nasa.gov/",
        "limitation": "Leak rates and recovery times are not real vehicle data.",
    },
    "water_recycler_glitch": {
        "title": "Water Recovery Systems",
        "summary": "Spacecraft water recovery systems recycle humidity condensate and other wastewater. Efficiency directly affects stored water needs.",
        "url": "https://www.nasa.gov/",
        "limitation": "Game recycler behaviour is an educational model.",
    },
    "equipment_wear": {
        "title": "Dust and Thermal Cycling",
        "summary": "Both lunar and Martian surface environments stress mechanisms through dust and temperature extremes.",
        "url": "https://www.nasa.gov/",
        "limitation": "Wear rates are not derived from a specific flight unit.",
    },
}


def _load_catalog() -> list[dict]:
    if not CATALOG_PATH.exists():
        return []
    rows = []
    with open(CATALOG_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def get_source_catalog() -> list[dict]:
    """Return the full provenance catalogue."""
    catalog = _load_catalog()
    if catalog:
        return catalog
    # Minimal fallback
    return [
        {
            "title": "NASA Space Apps Challenge — Junior Astronaut Mission Trainer",
            "agency": "NASA",
            "url": "https://www.spaceappschallenge.org/2026/challenges/junior-astronaut-mission-trainer/",
            "access_date": "2026-11",
            "units": "n/a",
            "use": "Challenge definition",
            "limits": "Challenge brief only; not operational data",
        },
        {
            "title": "NASA Artemis",
            "agency": "NASA",
            "url": "https://www.nasa.gov/specials/artemis/",
            "access_date": "2026-11",
            "units": "n/a",
            "use": "Moon mission context",
            "limits": "Public education pages",
        },
        {
            "title": "NASA Mars Exploration",
            "agency": "NASA",
            "url": "https://mars.nasa.gov/",
            "access_date": "2026-11",
            "units": "n/a",
            "use": "Mars environment context",
            "limits": "Public education pages",
        },
        {
            "title": "NASA DONKI",
            "agency": "NASA",
            "url": "https://ccmc.gsfc.nasa.gov/donki/",
            "access_date": "2026-11",
            "units": "varies",
            "use": "Space-weather educational context",
            "limits": "Not used for real dose calculations",
        },
    ]


def get_destination_facts(destination: str) -> list[dict]:
    dest = destination.title()
    return FALLBACK_FACTS.get(dest, [])


def get_event_context(event_id: str) -> dict:
    return EVENT_CONTEXT.get(event_id, {
        "title": "Training scenario",
        "summary": "This is an educational training event for the Junior Astronaut Mission Trainer challenge.",
        "url": "https://www.spaceappschallenge.org/",
        "limitation": "Not an operational NASA procedure.",
    })


def fetch_donki_notifications(limit: int = 3) -> list[dict]:
    """
    Optional live call to NASA DONKI (space weather).
    Returns a short list of recent notifications or empty list on failure.
    Uses DEMO_KEY or NASA_API_KEY from environment.
    """
    api_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    url = "https://api.nasa.gov/DONKI/notifications"
    params = {"type": "all", "api_key": api_key}
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        out = []
        for item in (data or [])[:limit]:
            out.append({
                "messageType": item.get("messageType"),
                "messageID": item.get("messageID"),
                "messageURL": item.get("messageURL"),
                "messageIssueTime": item.get("messageIssueTime"),
                "messageBody": (item.get("messageBody") or "")[:280],
            })
        return out
    except Exception:
        return []


def get_assumptions_panel() -> list[dict]:
    """Text for the in-app Simulation Assumptions panel."""
    return [
        {
            "topic": "Oxygen, water, food rates",
            "text": "Daily percentage drains are simplified educational parameters scaled by crew size and difficulty. They are not flight-certified consumable rates.",
        },
        {
            "topic": "Energy model",
            "text": "Energy combines a base habitat load, life-support load, optional food-production load, and a simplified solar contribution that is lower on Mars.",
        },
        {
            "topic": "Events",
            "text": "Events are training scenarios inspired by real environmental challenges (radiation, dust, power, leaks). Numeric effects are game balance choices.",
        },
        {
            "topic": "AI Mission Coach",
            "text": "The coach receives only the current state snapshot and approved fact snippets. It never changes resource numbers or mission outcome.",
        },
        {
            "topic": "Provenance",
            "text": "Every external reference used for context appears in the NASA Sources panel with title, URL and stated limitation.",
        },
    ]
