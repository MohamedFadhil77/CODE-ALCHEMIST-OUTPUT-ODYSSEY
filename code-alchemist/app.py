"""
Outpost Odyssey — Junior Astronaut Mission Trainer
CODE ALCHEMIST | NASA Space Apps Challenge 2026

Educational concept. Not an official NASA product.
"""

from __future__ import annotations
import streamlit as st

from simulation import (
    new_mission,
    advance_day,
    apply_event,
    get_status,
    pick_event_for_day,
    get_event_info,
    list_possible_actions,
)
from scoring import calculate_mission_score
from ai_advisor import get_advice
from nasa_data import (
    get_source_catalog,
    get_destination_facts,
    get_event_context,
    get_assumptions_panel,
    fetch_donki_notifications,
)
from scenarios import get_event_by_id, get_demo_story
from ui import (
    inject_css,
    draw_resource_gauges,
    resource_history_chart,
    score_breakdown_bars,
    event_alert_box,
    status_box,
    status_badge,
)

st.set_page_config(
    page_title="Outpost Odyssey — Junior Astronaut Mission Trainer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "mission" not in st.session_state:
    st.session_state.mission = None
if "page" not in st.session_state:
    st.session_state.page = "home"
if "coach_reply" not in st.session_state:
    st.session_state.coach_reply = None
if "pending_event_id" not in st.session_state:
    st.session_state.pending_event_id = None


def go(page: str):
    st.session_state.page = page


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🚀 Outpost Odyssey")
    st.caption("Junior Astronaut Mission Trainer")
    st.markdown("---")
    if st.button("🏠 Home", use_container_width=True):
        go("home")
    if st.button("🛰 New Mission", use_container_width=True):
        go("setup")
    if st.session_state.mission and st.session_state.mission["status"] == "active":
        if st.button("🎛 Mission Control", use_container_width=True):
            go("dashboard")
    if st.session_state.mission and st.session_state.mission["status"] in ("success", "failed"):
        if st.button("📋 Mission Report", use_container_width=True):
            go("report")
    if st.button("🤖 AI Mission Coach", use_container_width=True):
        go("coach")
    if st.button("📚 NASA Sources", use_container_width=True):
        go("sources")
    if st.button("⚙ Assumptions", use_container_width=True):
        go("assumptions")
    st.markdown("---")
    st.caption("Team Code Alchemist")
    st.caption("Educational concept · Not an official NASA product")


# ---------------------------------------------------------------------------
# HOME
# ---------------------------------------------------------------------------
if st.session_state.page == "home":
    st.markdown('<div class="mission-header">OUTPOST ODYSSEY</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">A Junior Astronaut Mission Trainer — run a Moon or Mars outpost and feel every trade-off.</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1.4, 1])
    with c1:
        st.markdown("### The challenge")
        st.write(
            "Space STEM content is often either too simple or too complex. "
            "Outpost Odyssey puts you in command of a small outpost where "
            "**life support, radiation shielding, power and food production** "
            "compete for limited resources."
        )
        st.markdown("### Core promise")
        st.success("**Every decision has a consequence.**")
        st.markdown(
            """
            - Choose Moon or Mars, crew size, duration and difficulty  
            - Allocate mass, energy and attention under pressure  
            - Face training emergencies (radiation, power, leaks, dust)  
            - Receive an explainable debrief after every mission  
            - Ask an AI Mission Coach for options — not magic answers  
            """
        )
        if st.button("Launch a new mission →", type="primary"):
            go("setup")
            st.rerun()

    with c2:
        st.markdown("### Decision loop")
        st.info(
            "**PLAN** → **DECIDE** → **SIMULATE** → **RESPOND** → **LEARN**"
        )
        demo = get_demo_story()
        st.markdown(f"**Suggested demo:** {demo['title']}")
        for step in demo["steps"]:
            st.markdown(f"- {step}")
        st.caption(demo["learning_goal"])

    st.markdown("---")
    st.markdown(
        "Built for the **NASA Space Apps Challenge 2026** · "
        "Team **Code Alchemist** · Six first-year students · One integrated app"
    )


# ---------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------
elif st.session_state.page == "setup":
    st.markdown('<div class="mission-header">MISSION SETUP</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Configure your outpost. Mission DNA changes the challenge.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        destination = st.selectbox("Destination", ["Moon", "Mars"], index=1)
        crew_size = st.slider("Crew size", 2, 6, 4)
    with col2:
        duration = st.select_slider("Mission duration (days)", options=[7, 14, 21, 30, 45, 60, 90], value=21)
        difficulty = st.selectbox("Difficulty", ["easy", "standard", "challenge"], index=1)

    facts = get_destination_facts(destination)
    with st.expander(f"Why {destination}? (NASA context)"):
        for f in facts:
            st.markdown(f"**{f['title']}** — {f['summary']}")
            st.caption(f"Source: {f['url']}")

    st.markdown("---")
    if st.button("Start mission", type="primary"):
        st.session_state.mission = new_mission(destination, crew_size, duration, difficulty)
        st.session_state.pending_event_id = None
        st.session_state.coach_reply = None
        go("dashboard")
        st.rerun()


# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------
elif st.session_state.page == "dashboard":
    m = st.session_state.mission
    if not m:
        st.warning("No active mission. Start one from Mission Setup.")
        if st.button("Go to setup"):
            go("setup")
            st.rerun()
        st.stop()

    # Header
    st.markdown(
        f'<div class="mission-header">{m["destination"].upper()} OUTPOST · DAY {m["day"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="subtitle">Crew {m["crew_size"]} · {m["duration_days"]} days · {m["difficulty"].title()} · '
        f'ID {m["mission_id"]} · {status_badge(get_status(m))}</div>',
        unsafe_allow_html=True,
    )

    # Status banner
    st_status = get_status(m)
    if st_status == "failed":
        status_box("failed", "A critical resource reached zero. Open the Mission Report for the debrief.")
        if st.button("View Mission Report"):
            # finalise score
            result = calculate_mission_score(m)
            m["score"] = result["score"]
            m["debrief"] = result
            st.session_state.mission = m
            go("report")
            st.rerun()
        st.stop()
    elif m["status"] == "success":
        status_box("success", "Mission duration completed. Open the report for your score and lessons.")
        if st.button("View Mission Report"):
            result = calculate_mission_score(m)
            m["score"] = result["score"]
            m["debrief"] = result
            st.session_state.mission = m
            go("report")
            st.rerun()
        st.stop()
    elif st_status == "critical":
        status_box("critical", "One or more resources are below 15%. Act carefully.")
    elif st_status == "warning":
        status_box("warning", "Resources are getting low. Consider conservation or system upgrades.")
    else:
        status_box("safe", "All systems within nominal training bands.")

    # Resource gauges
    draw_resource_gauges(m["resources"])

    # Systems row
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Shielding", f"Level {m['shielding_level']}/3")
    s2.metric("Backup power", "Online" if m["power_backup"] else "Offline")
    s3.metric("Food production", "Active" if m["food_production"] else "Inactive")
    s4.metric("Events faced", len(m["events_triggered"]))

    st.markdown("---")

    # Pending event handling
    if st.session_state.pending_event_id:
        eid = st.session_state.pending_event_id
        event = get_event_by_id(eid)
        if event:
            event_alert_box(event)
            ctx = get_event_context(eid)
            with st.expander("NASA / educational context"):
                st.write(ctx.get("summary", ""))
                st.caption(f"{ctx.get('title')} · {ctx.get('url')}")
                st.caption(f"Limitation: {ctx.get('limitation', '')}")

            responses = event.get("responses", ["no_action"])
            labels = {
                "no_action": "Do nothing (accept full effect)",
                "shelter": "Enter shelter / wait it out",
                "continue_work": "Continue outdoor work",
                "switch_backup": "Switch to backup power",
                "reduce_load": "Reduce non-essential loads",
                "seal_and_repair": "Seal and repair",
                "isolate_module": "Isolate affected module",
                "stow_arrays": "Stow solar arrays",
                "run_backup": "Run backup systems",
                "manual_override": "Manual override of recycler",
                "switch_to_reserve": "Switch to reserve water",
                "schedule_maintenance": "Schedule maintenance now",
                "defer": "Defer maintenance",
            }
            choice = st.radio(
                "Choose your response",
                responses,
                format_func=lambda x: labels.get(x, x.replace("_", " ").title()),
            )
            if st.button("Commit response", type="primary"):
                m = apply_event(m, eid, choice)
                st.session_state.mission = m
                st.session_state.pending_event_id = None
                st.rerun()
        else:
            st.session_state.pending_event_id = None

    else:
        # Normal day actions
        st.subheader("Today's decision")
        actions = list_possible_actions()
        action_ids = [a["id"] for a in actions]
        action_labels = {a["id"]: a["label"] for a in actions}
        chosen = st.selectbox(
            "Select an action for this day",
            action_ids,
            format_func=lambda x: action_labels.get(x, x),
        )
        c_adv, c_end = st.columns(2)
        with c_adv:
            if st.button("Advance one day", type="primary"):
                action = None if chosen == "none" else chosen
                m = advance_day(m, action)
                # Maybe trigger event for the new day
                if m["status"] == "active":
                    eid = pick_event_for_day(m)
                    if eid:
                        st.session_state.pending_event_id = eid
                st.session_state.mission = m
                st.rerun()
        with c_end:
            if st.button("End mission early"):
                m["status"] = "aborted"
                result = calculate_mission_score(m)
                m["score"] = result["score"]
                m["debrief"] = result
                st.session_state.mission = m
                go("report")
                st.rerun()

    # History chart
    st.markdown("### Resource history")
    resource_history_chart(m["history"])

    with st.expander("Day log"):
        for h in reversed(m["history"][-12:]):
            st.markdown(
                f"**Day {h['day']}** — {h.get('notes', '')} "
                f"(O₂ {h['resources']['oxygen_pct']:.0f}% · "
                f"H₂O {h['resources']['water_pct']:.0f}% · "
                f"Food {h['resources']['food_pct']:.0f}% · "
                f"PWR {h['resources']['energy_pct']:.0f}%)"
            )


# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
elif st.session_state.page == "report":
    m = st.session_state.mission
    if not m:
        st.warning("No mission data.")
        st.stop()

    if not m.get("debrief"):
        result = calculate_mission_score(m)
        m["score"] = result["score"]
        m["debrief"] = result
        st.session_state.mission = m

    d = m["debrief"]
    st.markdown('<div class="mission-header">MISSION DEBRIEF</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="subtitle">{m["destination"]} · {d["days_survived"]} days survived · '
        f'{d["events_count"]} events · {status_badge(d["status"])}</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Score", f"{d['score']:.1f} / 100")
    c2.metric("Grade", d["grade"].split("—")[0].strip())
    c3.metric("Outcome", d["status"].upper())

    st.markdown("### Score breakdown")
    score_breakdown_bars(d["breakdown"])

    st.markdown("### Lessons")
    for lesson in d["lessons"]:
        st.markdown(f"- {lesson}")

    st.markdown("### Final resources")
    draw_resource_gauges(m["resources"])

    st.markdown("### Full resource history")
    resource_history_chart(m["history"])

    if st.button("Start another mission"):
        st.session_state.mission = None
        st.session_state.pending_event_id = None
        st.session_state.coach_reply = None
        go("setup")
        st.rerun()


# ---------------------------------------------------------------------------
# AI COACH
# ---------------------------------------------------------------------------
elif st.session_state.page == "coach":
    st.markdown('<div class="mission-header">AI MISSION COACH</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Options and trade-offs — never invented facts. Simulation numbers stay untouched.</div>',
        unsafe_allow_html=True,
    )

    m = st.session_state.mission
    if not m:
        st.info("Start a mission first so the coach can see your state.")
        if st.button("New mission"):
            go("setup")
            st.rerun()
        st.stop()

    draw_resource_gauges(m["resources"])

    question = st.text_input(
        "Ask the coach",
        placeholder="e.g. What should I prioritise? Why is energy dropping? How do I handle a radiation alert?",
    )
    if st.button("Get advice", type="primary") or st.session_state.coach_reply:
        if question or st.session_state.coach_reply:
            if question:
                facts = get_destination_facts(m["destination"])
                if m.get("last_event"):
                    facts = facts + [get_event_context(m["last_event"])]
                reply = get_advice(m, question, facts)
                st.session_state.coach_reply = reply
            reply = st.session_state.coach_reply
            if reply:
                st.markdown("#### Summary")
                st.write(reply["summary"])
                st.markdown("#### Options")
                for opt in reply.get("options", []):
                    st.markdown(
                        f"**{opt.get('title', '')}**  \n"
                        f"Pros: {opt.get('pros', '')}  ·  Cons: {opt.get('cons', '')}"
                    )
                st.caption(f"Uncertainty: {reply.get('uncertainty', '')}")
                if reply.get("fallback"):
                    st.info("Using offline rule-based coach (Gemini key not configured or API unavailable).")
                else:
                    st.success("Response from Gemini educational coach.")
                with st.expander("Sources referenced"):
                    for s in reply.get("sources", []):
                        st.markdown(f"- {s}")


# ---------------------------------------------------------------------------
# NASA SOURCES
# ---------------------------------------------------------------------------
elif st.session_state.page == "sources":
    st.markdown('<div class="mission-header">NASA SOURCES & PROVENANCE</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Every external reference used for context. No NASA logos or endorsement claims.</div>',
        unsafe_allow_html=True,
    )

    catalog = get_source_catalog()
    for row in catalog:
        st.markdown(f"**{row.get('title', '')}**")
        st.caption(
            f"{row.get('agency', '')} · Accessed {row.get('access_date', '')} · "
            f"Use: {row.get('use', '')}"
        )
        st.markdown(f"[{row.get('url', '')}]({row.get('url', '')})")
        st.caption(f"Limits: {row.get('limits', '')}")
        st.markdown("---")

    st.markdown("### Optional live space-weather sample (NASA DONKI)")
    st.caption("Network call; may be empty if offline or rate-limited. Educational context only.")
    if st.button("Fetch recent DONKI notifications"):
        notes = fetch_donki_notifications(3)
        if not notes:
            st.warning("No notifications returned (offline, rate limit, or empty feed).")
        else:
            for n in notes:
                st.markdown(f"**{n.get('messageType')}** — {n.get('messageIssueTime')}")
                st.write(n.get("messageBody", "")[:400])
                if n.get("messageURL"):
                    st.caption(n["messageURL"])


# ---------------------------------------------------------------------------
# ASSUMPTIONS
# ---------------------------------------------------------------------------
elif st.session_state.page == "assumptions":
    st.markdown('<div class="mission-header">SIMULATION ASSUMPTIONS</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">All numeric rates are simplified educational parameters unless a NASA source is cited.</div>',
        unsafe_allow_html=True,
    )
    for item in get_assumptions_panel():
        st.markdown(f"**{item['topic']}**")
        st.write(item["text"])
        st.markdown("---")

    st.info(
        "This application is an educational concept created for the NASA Space Apps Challenge 2026. "
        "It is not an official NASA product and does not provide operational astronaut guidance."
    )
