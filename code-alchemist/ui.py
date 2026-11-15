"""
Outpost Odyssey — Streamlit UI helpers and page sections.
"""

from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
from typing import Any


def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Rajdhani:wght@400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Rajdhani', sans-serif;
        }
        h1, h2, h3 {
            font-family: 'Orbitron', sans-serif !important;
            letter-spacing: 0.04em;
        }
        .stApp {
            background: linear-gradient(165deg, #050a14 0%, #0b1526 40%, #0d1b2a 100%);
            color: #e8f1ff;
        }
        div[data-testid="stMetric"] {
            background: rgba(15, 30, 55, 0.85);
            border: 1px solid rgba(80, 140, 220, 0.35);
            border-radius: 12px;
            padding: 12px 16px;
        }
        div[data-testid="stMetric"] label {
            color: #8eb8ff !important;
        }
        .resource-card {
            background: rgba(12, 24, 44, 0.9);
            border: 1px solid rgba(70, 130, 210, 0.4);
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 10px;
        }
        .alert-box {
            background: rgba(120, 30, 30, 0.55);
            border-left: 4px solid #ff5c5c;
            padding: 14px 18px;
            border-radius: 8px;
            margin: 12px 0;
        }
        .safe-box {
            background: rgba(20, 70, 40, 0.45);
            border-left: 4px solid #3ddc84;
            padding: 14px 18px;
            border-radius: 8px;
            margin: 12px 0;
        }
        .warn-box {
            background: rgba(90, 70, 10, 0.5);
            border-left: 4px solid #ffc107;
            padding: 14px 18px;
            border-radius: 8px;
            margin: 12px 0;
        }
        .mission-header {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.6rem;
            color: #7ec8ff;
            margin-bottom: 0.2rem;
        }
        .subtitle {
            color: #9bb8d4;
            font-size: 0.95rem;
            margin-bottom: 1.2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    colors = {
        "safe": "🟢 SAFE",
        "warning": "🟡 WARNING",
        "critical": "🟠 CRITICAL",
        "failed": "🔴 FAILED",
        "success": "✅ SUCCESS",
        "active": "🔵 ACTIVE",
        "aborted": "⏹ ABORTED",
    }
    return colors.get(status, status.upper())


def resource_color(pct: float) -> str:
    if pct <= 0:
        return "#ff3b3b"
    if pct < 15:
        return "#ff6b35"
    if pct < 35:
        return "#ffc107"
    if pct < 60:
        return "#5dade2"
    return "#3ddc84"


def draw_resource_gauges(resources: dict[str, float]):
    cols = st.columns(5)
    labels = [
        ("oxygen_pct", "Oxygen", "O₂"),
        ("water_pct", "Water", "H₂O"),
        ("food_pct", "Food", "FOOD"),
        ("energy_pct", "Energy", "PWR"),
        ("equipment_pct", "Equipment", "EQP"),
    ]
    for col, (key, name, short) in zip(cols, labels):
        val = resources.get(key, 0)
        color = resource_color(val)
        with col:
            st.markdown(
                f"""
                <div class="resource-card" style="text-align:center;">
                    <div style="font-size:0.85rem;color:#8eb8ff;">{short}</div>
                    <div style="font-size:1.8rem;font-weight:700;color:{color};">{val:.0f}%</div>
                    <div style="font-size:0.8rem;color:#9bb8d4;">{name}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def resource_history_chart(history: list[dict]):
    if len(history) < 2:
        return
    days = [h["day"] for h in history]
    fig = go.Figure()
    for key, name, color in [
        ("oxygen_pct", "Oxygen", "#5dade2"),
        ("water_pct", "Water", "#48c9b0"),
        ("food_pct", "Food", "#f5b041"),
        ("energy_pct", "Energy", "#af7ac5"),
        ("equipment_pct", "Equipment", "#aab7b8"),
    ]:
        ys = [h["resources"].get(key, 0) for h in history]
        fig.add_trace(go.Scatter(
            x=days, y=ys, mode="lines+markers", name=name,
            line=dict(color=color, width=2),
            marker=dict(size=5),
        ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,18,32,0.8)",
        margin=dict(l=40, r=20, t=30, b=40),
        height=320,
        legend=dict(orientation="h", y=1.12),
        xaxis_title="Mission day",
        yaxis_title="Resource %",
        yaxis=dict(range=[0, 105]),
        font=dict(family="Rajdhani", color="#cde0f7"),
    )
    st.plotly_chart(fig, use_container_width=True)


def score_breakdown_bars(breakdown: dict[str, float]):
    labels = list(breakdown.keys())
    values = list(breakdown.values())
    fig = go.Figure(go.Bar(
        x=values,
        y=[l.replace("_", " ").title() for l in labels],
        orientation="h",
        marker_color="#3d8bfd",
        text=[f"{v:.1f}" for v in values],
        textposition="auto",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,18,32,0.8)",
        height=280,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Points",
        font=dict(family="Rajdhani", color="#cde0f7"),
    )
    st.plotly_chart(fig, use_container_width=True)


def event_alert_box(event: dict):
    st.markdown(
        f"""
        <div class="alert-box">
            <strong style="font-size:1.15rem;">⚠ {event.get('name', 'Event')}</strong><br>
            <span style="color:#ffd0d0;">{event.get('description', '')}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_box(status: str, message: str = ""):
    cls = "safe-box" if status in ("safe", "success") else ("warn-box" if status == "warning" else "alert-box")
    st.markdown(
        f'<div class="{cls}"><strong>{status_badge(status)}</strong> {message}</div>',
        unsafe_allow_html=True,
    )
