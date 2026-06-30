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
# BRACKET DE ELIMINATORIAS  ← AQUÍ AL PRINCIPIO
# ─────────────────────────────────────────
st.markdown("### 🏆 Cuadro de eliminatorias")
st.markdown("Cruces desde dieciseisavos hasta la final. Se completan automáticamente a medida que avanza el torneo.")

@st.cache_data(ttl=300)
def load_bracket():
    try:
        return requests.get(f"{API_URL}/bracket", timeout=5).json()
    except Exception:
        return {}

bracket = load_bracket()

STAGE_LABELS = {
    "LAST_32": "Dieciseisavos",
    "LAST_16": "Octavos",
    "QUARTER_FINALS": "Cuartos",
    "SEMI_FINALS": "Semifinales",
    "THIRD_PLACE": "3er puesto",
    "FINAL": "Final",
}

if not bracket:
    st.info("Cuadro de eliminatorias no disponible todavía.")
else:
    columns_html = ""
    for stage_key, stage_label in STAGE_LABELS.items():
        matches = bracket.get(stage_key, [])
        if not matches:
            continue
        matches_html = ""
        for m in matches:
            home = m.get("home_team", "TBD")
            away = m.get("away_team", "TBD")
            h_score = m.get("home_score")
            a_score = m.get("away_score")
            home_winner = h_score is not None and a_score is not None and h_score > a_score
            away_winner = h_score is not None and a_score is not None and a_score > h_score
            home_color = "#2EA043" if home_winner else "#8B949E" if home == "TBD" else "white"
            away_color = "#2EA043" if away_winner else "#8B949E" if away == "TBD" else "white"
            home_score_str = h_score if h_score is not None else ""
            away_score_str = a_score if a_score is not None else ""
            matches_html += f"""
            <div style="
                background: #161B22;
                border: 1px solid #30363D;
                border-radius: 8px;
                padding: 10px 12px;
                margin-bottom: 16px;
                min-width: 180px;
            ">
                <div style="display:flex; justify-content:space-between; align-items:center; padding:4px 0;">
                    <span style="color:{home_color}; font-size:13px; font-weight:{'bold' if home_winner else 'normal'};">{home}</span>
                    <span style="color:#E8C84A; font-weight:bold; font-size:13px;">{home_score_str}</span>
                </div>
                <div style="height:1px; background:#30363D; margin:2px 0;"></div>
                <div style="display:flex; justify-content:space-between; align-items:center; padding:4px 0;">
                    <span style="color:{away_color}; font-size:13px; font-weight:{'bold' if away_winner else 'normal'};">{away}</span>
                    <span style="color:#E8C84A; font-weight:bold; font-size:13px;">{away_score_str}</span>
                </div>
            </div>
            """
        columns_html += f"""
        <div style="min-width: 200px; margin-right: 24px;">
            <div style="
                color: #E8C84A;
                font-weight: bold;
                font-size: 14px;
                text-align: center;
                margin-bottom: 12px;
                border-bottom: 2px solid #E8C84A;
                padding-bottom: 6px;
            ">{stage_label}</div>
            {matches_html}
        </div>
        """
    st.markdown(f"""
    <div style="display: flex; overflow-x: auto; padding: 16px 0; gap: 0;">
        {columns_html}
    </div>
    """, unsafe_allow_html=True)
    st.caption("🟢 Verde = equipo que avanzó · ⚪ Gris = por determinar")

st.divider()

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