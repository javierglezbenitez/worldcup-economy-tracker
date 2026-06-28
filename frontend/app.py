import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="World Cup Economy Tracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown("""
<div style="text-align: center; padding: 20px 0;">
    <h1 style="color: #E8C84A; font-size: 48px; margin: 0;">⚽ World Cup Economy Tracker</h1>
    <p style="color: #8B949E; font-size: 18px; margin-top: 8px;">
        Uncovering hidden economic correlations during the 2026 FIFA World Cup
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────
# MÉTRICAS RÁPIDAS
# ─────────────────────────────────────────
try:
    health = requests.get(f"{API_URL}/health", timeout=5).json()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("⚽ Partidos", health["matches_count"])
    with col2:
        st.metric("🎯 Eventos", health["events_count"])
    with col3:
        st.metric("📈 Snapshots", health["snapshots_count"])
    with col4:
        st.metric("📰 Noticias", health["news_count"])

except Exception:
    st.error("⚠️ No se puede conectar con el backend. Asegúrate de que FastAPI está corriendo.")
    st.stop()

st.divider()

# ─────────────────────────────────────────
# RESUMEN DE SPONSORS
# ─────────────────────────────────────────
st.subheader("📈 Sponsors en tiempo real")

try:
    snapshots = requests.get(f"{API_URL}/stocks/snapshots", timeout=5).json()
    cols = st.columns(len(snapshots))
    for i, stock in enumerate(snapshots):
        with cols[i]:
            trend = stock["trend"]
            color = "#2EA043" if trend == "UP" else "#F85149" if trend == "DOWN" else "#8B949E"
            arrow = "▲" if trend == "UP" else "▼" if trend == "DOWN" else "●"
            st.markdown(f"""
            <div style="
                background: #161B22;
                border: 1px solid #30363D;
                border-radius: 10px;
                padding: 12px;
                text-align: center;
            ">
                <div style="color: #8B949E; font-size: 11px;">{stock['ticker']}</div>
                <div style="font-size: 13px; font-weight: bold;">{stock['company_name']}</div>
                <div style="font-size: 20px; font-weight: bold;">${stock['price']:.2f}</div>
                <div style="color: {color};">{arrow} {stock['change_pct']:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
except Exception as e:
    st.warning(f"No se pudieron cargar los stocks: {e}")

st.divider()

# ─────────────────────────────────────────
# RESUMEN DE SENTIMIENTO
# ─────────────────────────────────────────
st.subheader("📰 Pulso económico del Mundial")

try:
    summaries = requests.get(f"{API_URL}/sentiment/summary", timeout=5).json()
    cols = st.columns(len(summaries))
    for i, s in enumerate(summaries):
        with cols[i]:
            icon = "🟢" if s["sentiment_label"] == "POSITIVE" else "🔴" if s["sentiment_label"] == "NEGATIVE" else "⚪"
            color = "#2EA043" if s["sentiment_label"] == "POSITIVE" else "#F85149" if s["sentiment_label"] == "NEGATIVE" else "#8B949E"
            st.markdown(f"""
            <div style="
                background: #161B22;
                border: 1px solid #30363D;
                border-radius: 10px;
                padding: 12px;
                text-align: center;
            ">
                <div style="font-size: 11px; color: #8B949E;">{s['category']}</div>
                <div style="font-size: 24px;">{icon}</div>
                <div style="color: {color}; font-weight: bold; font-size: 13px;">{s['sentiment_label']}</div>
                <div style="font-size: 11px; color: #8B949E;">score: {s['avg_sentiment']:.2f}</div>
                <div style="font-size: 11px; color: #8B949E;">{s['total_articles']} artículos</div>
            </div>
            """, unsafe_allow_html=True)
except Exception as e:
    st.warning(f"No se pudo cargar el sentimiento: {e}")

st.divider()

# ─────────────────────────────────────────
# ÚLTIMOS PARTIDOS
# ─────────────────────────────────────────
st.subheader("⚽ Últimos resultados")

try:
    matches = requests.get(f"{API_URL}/matches?status=FINISHED", timeout=5).json()
    recent = matches[-6:][::-1]  # Últimos 6 partidos

    for match in recent:
        col1, col2, col3 = st.columns([3, 1, 3])
        with col1:
            st.markdown(f"<div style='text-align:right; font-size:18px; font-weight:bold;'>{match['home_team']}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='text-align:center; font-size:20px; font-weight:bold; color:#E8C84A;'>{match['home_score']} - {match['away_score']}</div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div style='text-align:left; font-size:18px; font-weight:bold;'>{match['away_team']}</div>", unsafe_allow_html=True)

except Exception as e:
    st.warning(f"No se pudieron cargar los partidos: {e}")

# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚽ World Cup Economy")
    st.markdown("---")
    st.markdown("### 🔗 Navegación")
    st.markdown("Usa el menú de arriba para explorar:")
    st.markdown("- 🏆 Clasificaciones")
    st.markdown("- ⚽ Resultados")
    st.markdown("- 📈 Sponsors")
    st.markdown("- 📰 Sentimiento")
    st.markdown("- 🔬 Correlaciones")
    st.markdown("---")
    st.markdown("### ⚙️ Estado del sistema")
    if st.button("🔄 Actualizar datos"):
        try:
            requests.post(f"{API_URL}/admin/sync", timeout=30)
            st.success("Datos actualizados")
            st.rerun()
        except Exception:
            st.error("Error al actualizar")