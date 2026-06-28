import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Resultados — World Cup Economy Tracker",
    page_icon="⚽",
    layout="wide",
)

st.markdown("# ⚽ Resultados y Partidos")
st.markdown("Resultados en tiempo real y próximos partidos del Mundial 2026")
st.divider()


# ─────────────────────────────────────────
# CARGAR DATOS
# ─────────────────────────────────────────
@st.cache_data(ttl=60)
def load_matches(status: str = None):
    try:
        url = f"{API_URL}/matches"
        if status:
            url += f"?status={status}"
        return requests.get(url, timeout=5).json()
    except Exception:
        return []


# ─────────────────────────────────────────
# TABS
# ─────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🔴 En Vivo", "✅ Finalizados", "🕐 Próximos"])


def render_match(match: dict):
    """Renderiza una tarjeta de partido"""
    stage = match.get("stage", "").replace("_", " ")
    group = match.get("group", "")
    group_str = f" — {group}" if group else ""

    home = match["home_team"]
    away = match["away_team"]
    h_score = match["home_score"]
    a_score = match["away_score"]
    status = match["status"]

    status_color = "#F85149" if status == "LIVE" else "#2EA043" if status == "FINISHED" else "#8B949E"
    status_icon = "🔴" if status == "LIVE" else "✅" if status == "FINISHED" else "🕐"

    score_str = f"{h_score} - {a_score}" if h_score is not None else "vs"

    # Kickoff en hora local
    kickoff = match.get("kickoff_utc", "")
    if kickoff:
        try:
            dt = datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
            kickoff_str = dt.strftime("%d %b %Y — %H:%M UTC")
        except Exception:
            kickoff_str = kickoff
    else:
        kickoff_str = ""

    st.markdown(f"""
    <div style="
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 16px 20px;
        margin: 8px 0;
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
        ">
            <span style="color: #8B949E; font-size: 12px;">{stage}{group_str}</span>
            <span style="color: {status_color}; font-size: 12px;">{status_icon} {status}</span>
            <span style="color: #8B949E; font-size: 12px;">{kickoff_str}</span>
        </div>
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 8px;
        ">
            <div style="flex: 1; text-align: right;">
                <span style="font-size: 20px; font-weight: bold;">{home}</span>
            </div>
            <div style="padding: 0 24px; text-align: center;">
                <span style="font-size: 28px; font-weight: bold; color: #E8C84A;">{score_str}</span>
            </div>
            <div style="flex: 1; text-align: left;">
                <span style="font-size: 20px; font-weight: bold;">{away}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# TAB 1 — EN VIVO
# ─────────────────────────────────────────
with tab1:
    live = load_matches("LIVE")
    if not live:
        st.info("No hay partidos en vivo ahora mismo. ¡Vuelve cuando empiece el siguiente partido!")
    else:
        st.markdown(f"### 🔴 {len(live)} partido(s) en vivo")
        for match in live:
            render_match(match)


# ─────────────────────────────────────────
# TAB 2 — FINALIZADOS
# ─────────────────────────────────────────
with tab2:
    finished = load_matches("FINISHED")

    if not finished:
        st.warning("No hay partidos finalizados todavía")
    else:
        # Filtros
        col1, col2 = st.columns([2, 1])
        with col1:
            stages = list(set(m.get("stage", "") for m in finished))
            stages = ["Todos"] + sorted([s for s in stages if s])
            selected_stage = st.selectbox("Filtrar por fase", stages)
        with col2:
            st.metric("Total finalizados", len(finished))

        # Aplicar filtro
        filtered = finished
        if selected_stage != "Todos":
            filtered = [m for m in finished if m.get("stage") == selected_stage]

        # Mostrar partidos más recientes primero
        filtered = filtered[::-1]

        st.markdown(f"Mostrando **{len(filtered)}** partidos")
        for match in filtered:
            render_match(match)


# ─────────────────────────────────────────
# TAB 3 — PRÓXIMOS
# ─────────────────────────────────────────
with tab3:
    scheduled = load_matches("TIMED")

    if not scheduled:
        st.info("No hay próximos partidos programados todavía")
    else:
        st.markdown(f"### 🕐 Próximos {len(scheduled)} partidos")

        # Agrupar por fecha
        matches_by_date = {}
        for match in scheduled:
            kickoff = match.get("kickoff_utc", "")
            try:
                dt = datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
                date_str = dt.strftime("%A %d %B %Y")
            except Exception:
                date_str = "Fecha por confirmar"

            if date_str not in matches_by_date:
                matches_by_date[date_str] = []
            matches_by_date[date_str].append(match)

        for date_str, day_matches in matches_by_date.items():
            st.markdown(f"#### 📅 {date_str}")
            for match in day_matches:
                render_match(match)