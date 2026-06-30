import streamlit as st
import requests
from datetime import datetime

API_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="World Cup Economy Tracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLORS = {
    "gold": "#E8C84A",
    "green": "#2EA043",
    "red": "#F85149",
    "gray": "#8B949E",
    "bg": "#0D1117",
    "card": "#161B22",
}

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

# ─────────────────────────────────────────
# TITULAR DEL DÍA (IA)
# ─────────────────────────────────────────
@st.cache_data(ttl=900)  # 15 minutos
def load_headline():
    try:
        return requests.get(f"{API_URL}/headline", timeout=20).json().get("headline", "")
    except Exception:
        return ""

headline = load_headline()

if headline:
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #161B22 0%, #1c2230 100%);
        border-left: 4px solid {COLORS['gold']};
        border-radius: 12px;
        padding: 24px 28px;
        margin: 12px 0 24px 0;
    ">
        <div style="color: {COLORS['gold']}; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin-bottom: 8px;">
            📰 TITULAR DEL MOMENTO · ANALISTA IA
        </div>
        <div style="color: white; font-size: 22px; font-weight: bold; line-height: 1.4;">
            {headline}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────
# TIMELINE NARRATIVO
# ─────────────────────────────────────────
st.markdown("### 🕐 Línea temporal — Fútbol y economía en tiempo real")
st.caption("Los últimos hitos deportivos y económicos, mezclados en orden cronológico")

@st.cache_data(ttl=120)  # 2 minutos
def load_timeline():
    try:
        return requests.get(f"{API_URL}/timeline", timeout=10).json()
    except Exception:
        return []

timeline = load_timeline()

if not timeline:
    st.info("⏳ Aún no hay suficientes hitos para construir la línea temporal.")
else:
    for item in timeline:
        item_type = item.get("type", "")
        text = item.get("text", "")
        timestamp = item.get("timestamp", "")

        try:
            dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
            time_str = dt.strftime("%d %b — %H:%M UTC")
        except Exception:
            time_str = ""

        border_color = COLORS["green"] if item_type == "goal" else COLORS["gray"]

        st.markdown(f"""
        <div style="
            display: flex;
            align-items: flex-start;
            margin: 4px 0;
            padding: 12px 16px;
            background: {COLORS['card']};
            border-left: 3px solid {border_color};
            border-radius: 6px;
        ">
            <div style="flex: 1;">
                <span style="font-size: 14px;">{text}</span>
            </div>
            <div style="color: {COLORS['gray']}; font-size: 11px; white-space: nowrap; margin-left: 16px;">
                {time_str}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────
# MÉTRICAS RÁPIDAS (compactas, debajo del timeline)
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
    st.error("⚠️ No se puede conectar con el backend. Asegúrate de que está corriendo.")
    st.stop()

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
    st.markdown("- 🤖 Chatbot")
    st.markdown("---")
    st.markdown("### ⚙️ Estado del sistema")
    if st.button("🔄 Actualizar datos"):
        try:
            requests.post(f"{API_URL}/admin/sync", timeout=30)
            st.cache_data.clear()
            st.success("Datos actualizados")
            st.rerun()
        except Exception:
            st.error("Error al actualizar")