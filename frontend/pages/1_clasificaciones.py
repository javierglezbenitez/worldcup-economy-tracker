import streamlit as st
import requests
import plotly.express as px
import pandas as pd

import streamlit as st
API_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Clasificaciones — World Cup Economy Tracker",
    page_icon="🏆",
    layout="wide",
)

st.markdown("# 🏆 Clasificaciones")
st.markdown("Clasificaciones en tiempo real de los 12 grupos del Mundial 2026")
st.divider()

# ─────────────────────────────────────────
# CARGAR DATOS
# ─────────────────────────────────────────
@st.cache_data(ttl=300)  # Cache 5 minutos
def load_standings():
    try:
        return requests.get(f"{API_URL}/standings", timeout=5).json()
    except Exception:
        return {}

standings = load_standings()

if not standings:
    st.error("No se pudieron cargar las clasificaciones")
    st.stop()

# ─────────────────────────────────────────
# SELECTOR DE GRUPO
# ─────────────────────────────────────────
groups = list(standings.keys())
selected_group = st.selectbox("Selecciona un grupo", groups, index=0)

st.divider()

# ─────────────────────────────────────────
# VISTA DE GRUPO SELECCIONADO
# ─────────────────────────────────────────
table = standings[selected_group]
df = pd.DataFrame(table)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(f"### {selected_group}")

    # Tabla estilizada
    for row in table:
        pos = row["position"]
        team = row["team"]
        pts = row["points"]
        played = row["played"]
        won = row["won"]
        draw = row["draw"]
        lost = row["lost"]
        gf = row["goals_for"]
        ga = row["goals_against"]
        gd = row["goal_difference"]

        # Color según posición (clasificados vs eliminados)
        if pos <= 2:
            border_color = "#2EA043"  # Verde — clasificado
        else:
            border_color = "#30363D"  # Gris — eliminado

        st.markdown(f"""
        <div style="
            background: #161B22;
            border-left: 4px solid {border_color};
            border-radius: 8px;
            padding: 12px 16px;
            margin: 6px 0;
            display: flex;
            align-items: center;
        ">
            <span style="color: #8B949E; width: 24px; font-size: 14px;">{pos}</span>
            <span style="font-weight: bold; flex: 1; font-size: 16px; margin-left: 8px;">{team}</span>
            <span style="color: #8B949E; font-size: 13px; margin: 0 8px;">PJ {played}</span>
            <span style="color: #8B949E; font-size: 13px; margin: 0 8px;">G {won}</span>
            <span style="color: #8B949E; font-size: 13px; margin: 0 8px;">E {draw}</span>
            <span style="color: #8B949E; font-size: 13px; margin: 0 8px;">P {lost}</span>
            <span style="color: #8B949E; font-size: 13px; margin: 0 8px;">GF {gf}</span>
            <span style="color: #8B949E; font-size: 13px; margin: 0 8px;">GC {ga}</span>
            <span style="color: #E8C84A; font-weight: bold; font-size: 18px; margin-left: 12px;">{pts} pts</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top: 8px; font-size: 12px; color: #8B949E;">
        <span style="border-left: 3px solid #2EA043; padding-left: 6px;">Clasificado a siguiente ronda</span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Gráfico de puntos
    fig_points = px.bar(
        df,
        x="team",
        y="points",
        color="points",
        color_continuous_scale=["#30363D", "#E8C84A"],
        title="Puntos por equipo",
        labels={"team": "", "points": "Puntos"},
    )
    fig_points.update_layout(
        plot_bgcolor="#0D1117",
        paper_bgcolor="#161B22",
        font_color="#8B949E",
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(t=40, b=0),
    )
    st.plotly_chart(fig_points, use_container_width=True)

    # Gráfico de goles
    fig_goals = px.bar(
        df,
        x="team",
        y=["goals_for", "goals_against"],
        barmode="group",
        title="Goles a favor vs en contra",
        labels={"team": "", "value": "Goles", "variable": ""},
        color_discrete_map={
            "goals_for": "#2EA043",
            "goals_against": "#F85149"
        }
    )
    fig_goals.update_layout(
        plot_bgcolor="#0D1117",
        paper_bgcolor="#161B22",
        font_color="#8B949E",
        margin=dict(t=40, b=0),
    )
    st.plotly_chart(fig_goals, use_container_width=True)

st.divider()

# ─────────────────────────────────────────
# VISTA GLOBAL — TODOS LOS GRUPOS
# ─────────────────────────────────────────
st.markdown("### 🌍 Vista global — Todos los grupos")

# Mostrar todos los grupos en grid 3x4
group_items = list(standings.items())
rows = [group_items[i:i+3] for i in range(0, len(group_items), 3)]

for row in rows:
    cols = st.columns(3)
    for col, (group_name, table) in zip(cols, row):
        with col:
            st.markdown(f"**{group_name}**")
            for team_row in table:
                pos_color = "#2EA043" if team_row["position"] <= 2 else "#8B949E"
                st.markdown(f"""
                <div style="
                    display: flex;
                    justify-content: space-between;
                    padding: 4px 8px;
                    border-radius: 4px;
                    background: #161B22;
                    margin: 2px 0;
                    font-size: 13px;
                ">
                    <span style="color: {pos_color};">{team_row['position']}. {team_row['team']}</span>
                    <span style="color: #E8C84A; font-weight: bold;">{team_row['points']} pts</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)