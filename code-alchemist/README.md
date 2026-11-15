# Outpost Odyssey
**Junior Astronaut Mission Trainer**  
NASA Space Apps Challenge 2026 · Team Code Alchemist

Educational concept. **Not an official NASA product.**

---

## What it is

An interactive Moon / Mars outpost simulator built with Python and Streamlit.  
Players manage oxygen, water, food, energy and equipment while responding to training emergencies. Every decision has a visible consequence. An AI Mission Coach (Gemini, with offline fallback) explains options and trade-offs but never changes the numbers.

**Core loop:** PLAN → DECIDE → SIMULATE → RESPOND → LEARN

---

## Features (MVP)

- Moon or Mars mission setup (crew, duration, difficulty)
- Deterministic resource simulation
- Decision actions (shielding, backup power, food production, conservation, repairs)
- Training event cards (radiation, power fault, oxygen leak, dust storm, water recycler, equipment wear)
- Mission dashboard with gauges and history charts
- Explainable end-of-mission report and score
- AI Mission Coach (Gemini + rule-based fallback)
- NASA sources / provenance panel
- Simulation assumptions panel

---

## Quick start

```bash
# 1. Clone / enter the project
cd code-alchemist

# 2. Create virtual environment (recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Gemini API key for the AI coach
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=...

# 5. Run the app
streamlit run app.py
```

Open the URL shown in the terminal (usually http://localhost:8501).

---

## Tests

```bash
python -m pytest tests/ -v
```

---

## Project structure

```
code-alchemist/
├── app.py              # Streamlit entry point & integration
├── simulation.py       # Resource engine & events
├── scoring.py          # Mission score & lessons
├── ai_advisor.py       # Gemini coach + offline fallback
├── nasa_data.py        # Sources, facts, optional DONKI call
├── scenarios.py        # Event catalogue helpers
├── ui.py               # Shared UI components & styling
├── data/
│   └── source_catalog.csv
├── docs/
│   └── PROJECT_CONTRACT.md
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

---

## Team (six workstreams)

| Role | Focus |
|------|--------|
| Team lead & integration | app.py, architecture, GitHub |
| Simulation | simulation.py, scoring.py |
| UI | ui.py, pages/, components/ |
| AI | ai_advisor.py, prompts/ |
| NASA data | nasa_data.py, scenarios.py, source catalog |
| QA & docs | tests/, README, docs/ |

---

## NASA grounding & responsible use

- Challenge brief, Artemis and Mars public pages, NASA Open APIs / DONKI used for **educational context**.
- All simulation rates are labelled as **simplified educational assumptions** unless a specific NASA source is cited.
- Provenance panel lists title, URL, access date, use and limits.
- No NASA logos or endorsement claims.
- AI never invents NASA measurements and never modifies resource values or scores.

---

## Demo story

1. Start a Mars mission, crew 4, 21 days, standard difficulty.  
2. Run a few nominal days; start food production when energy allows.  
3. When a radiation or power event appears, choose the protective response.  
4. Finish (or fail) and open the debrief.  
5. Ask the AI coach why a resource became the bottleneck.

The core game works fully offline; only the optional Gemini coach and live DONKI fetch need the network.

---

## Licence & disclosure

Educational project for NASA Space Apps Challenge 2026.  
AI-assisted content and code generation were used in development and are disclosed as required by event rules.  
Re-check current challenge rules, API terms and deadlines before submission.
