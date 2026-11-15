"""
Outpost Odyssey — AI Mission Coach
Uses Gemini when available; otherwise deterministic rule-based hints.
The AI NEVER modifies simulation state or scores.
"""

from __future__ import annotations
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Rule-based fallback (always available)
# ---------------------------------------------------------------------------
def _rule_based_advice(state: dict, question: str) -> dict[str, Any]:
    res = state.get("resources", {})
    dest = state.get("destination", "Moon")
    day = state.get("day", 1)
    status = state.get("status", "active")
    q = (question or "").lower()

    # Identify bottleneck
    bottleneck = min(res, key=res.get) if res else "energy_pct"
    bot_val = res.get(bottleneck, 0)

    summary_parts = [
        f"Day {day} on {dest}. Overall status: {status}.",
        f"Lowest resource right now is {bottleneck.replace('_pct', '')} at {bot_val:.0f}%.",
    ]

    options = []

    if "oxygen" in q or bottleneck == "oxygen_pct":
        options.append({
            "title": "Protect the cabin atmosphere",
            "pros": "Stops further loss; keeps crew safe",
            "cons": "May cost energy or delay other tasks",
        })
        options.append({
            "title": "Reduce non-essential activity",
            "pros": "Lowers metabolic and system demand",
            "cons": "Slower progress on science or maintenance",
        })
        summary_parts.append("Oxygen is critical. Prioritise leak isolation or reduced activity before other upgrades.")

    elif "water" in q or bottleneck == "water_pct":
        options.append({
            "title": "Check the water recovery system",
            "pros": "Restores recycling efficiency",
            "cons": "Uses energy and crew time",
        })
        options.append({
            "title": "Tighten water-use protocols",
            "pros": "Immediate reduction in demand",
            "cons": "Crew comfort impact",
        })
        summary_parts.append("Water is the constraint. Recycling efficiency and crew usage both matter.")

    elif "food" in q or bottleneck == "food_pct":
        options.append({
            "title": "Start or expand food production",
            "pros": "Reduces long-term food drain",
            "cons": "Needs water and steady power",
        })
        options.append({
            "title": "Short-term rationing",
            "pros": "Buys days of margin",
            "cons": "Does not solve the production gap",
        })
        summary_parts.append("Food stores are low. Production systems help only if power and water can support them.")

    elif "energy" in q or "power" in q or bottleneck == "energy_pct":
        options.append({
            "title": "Shed non-essential loads",
            "pros": "Protects life support",
            "cons": "May pause science or production",
        })
        options.append({
            "title": "Bring backup power online",
            "pros": "Adds resilience for the next event",
            "cons": "Installation cost in energy/equipment",
        })
        summary_parts.append("Power is the bottleneck. Life support must be protected first.")

    elif "radiation" in q or "solar" in q or "shield" in q:
        options.append({
            "title": "Shelter and wait out the event",
            "pros": "Lowest exposure",
            "cons": "Uses stored energy and may delay tasks",
        })
        options.append({
            "title": "Continue limited outdoor work",
            "pros": "Keeps schedule",
            "cons": "Higher equipment and potential exposure cost",
        })
        summary_parts.append("Radiation events are training scenarios. Shielding level and operational choices both matter.")

    else:
        options.append({
            "title": "Address the current lowest resource",
            "pros": "Prevents cascade failure",
            "cons": "May delay other upgrades",
        })
        options.append({
            "title": "Invest in a resilience system",
            "pros": "Shielding, backup power or food production",
            "cons": "Upfront resource cost",
        })
        summary_parts.append("Ask about a specific resource or the current event for more focused options.")

    if not options:
        options = [{
            "title": "Review the mission dashboard",
            "pros": "See exact numbers",
            "cons": "None",
        }]

    return {
        "summary": " ".join(summary_parts),
        "options": options[:3],
        "sources": ["Built-in educational rules (no external API call)"],
        "uncertainty": "These are simplified training suggestions, not operational NASA procedures.",
        "fallback": True,
    }


def _call_gemini(state: dict, question: str, approved_facts: list[dict] | None) -> dict[str, Any] | None:
    """Attempt a Gemini call. Returns None on any failure."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.startswith("your_"):
        return None

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        facts_text = ""
        if approved_facts:
            facts_text = "Approved facts:\n" + "\n".join(
                f"- {f.get('title', '')}: {f.get('summary', f.get('text', ''))}" for f in approved_facts[:6]
            )

        res = state.get("resources", {})
        prompt = f"""You are an educational AI Mission Coach for a student space-outpost simulation (Outpost Odyssey).
You give options and trade-offs only. You never invent NASA measurements or change game numbers.
You never claim to give real astronaut operational advice.

Current mission snapshot:
- Destination: {state.get('destination')}
- Day: {state.get('day')} / {state.get('duration_days')}
- Crew: {state.get('crew_size')}
- Difficulty: {state.get('difficulty')}
- Status: {state.get('status')}
- Oxygen: {res.get('oxygen_pct', 0):.0f}%
- Water: {res.get('water_pct', 0):.0f}%
- Food: {res.get('food_pct', 0):.0f}%
- Energy: {res.get('energy_pct', 0):.0f}%
- Equipment: {res.get('equipment_pct', 0):.0f}%
- Shielding level: {state.get('shielding_level')}
- Power backup: {state.get('power_backup')}
- Food production: {state.get('food_production')}
- Last event: {state.get('last_event')}
- Events so far: {state.get('events_triggered')}

{facts_text}

Student question: {question}

Respond in this exact structure (plain text):
SUMMARY: <2-3 sentences>
OPTION 1: <title> | PROS: <short> | CONS: <short>
OPTION 2: <title> | PROS: <short> | CONS: <short>
OPTION 3: <title> | PROS: <short> | CONS: <short>
UNCERTAINTY: <one sentence about what is simplified or unknown>
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = (response.text or "").strip()
        if not text:
            return None

        # Lightweight parse
        summary = ""
        options = []
        uncertainty = "Educational simulation; not operational advice."
        for line in text.splitlines():
            line = line.strip()
            if line.upper().startswith("SUMMARY:"):
                summary = line.split(":", 1)[1].strip()
            elif line.upper().startswith("OPTION"):
                parts = [p.strip() for p in line.split("|")]
                title = parts[0].split(":", 1)[-1].strip() if ":" in parts[0] else parts[0]
                pros = cons = ""
                for p in parts[1:]:
                    if p.upper().startswith("PROS"):
                        pros = p.split(":", 1)[-1].strip()
                    elif p.upper().startswith("CONS"):
                        cons = p.split(":", 1)[-1].strip()
                options.append({"title": title, "pros": pros, "cons": cons})
            elif line.upper().startswith("UNCERTAINTY:"):
                uncertainty = line.split(":", 1)[1].strip()

        if not summary:
            summary = text[:400]

        return {
            "summary": summary,
            "options": options[:3] or [{"title": "Review resources", "pros": "Clarity", "cons": "None"}],
            "sources": ["Gemini (educational coach)", "Approved fact pack only"],
            "uncertainty": uncertainty,
            "fallback": False,
        }
    except Exception:
        return None


def get_advice(
    state: dict,
    question: str,
    approved_facts: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Main entry point used by the UI.
    Tries Gemini; falls back to deterministic rules.
    """
    if not question or not str(question).strip():
        question = "What should I prioritise right now?"

    result = _call_gemini(state, question, approved_facts)
    if result is not None:
        return result
    return _rule_based_advice(state, question)
