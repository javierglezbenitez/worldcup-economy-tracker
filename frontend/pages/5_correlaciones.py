import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

import streamlit as st
API_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Correlaciones — World Cup Economy Tracker",
    page_icon="🔬",
    layout="wide",
)

st.markdown("# 🔬 Correlaciones Económicas")
st.markdown("¿Qué le pasa a la economía cuando ocurre algo en el campo?")
st.divider()

COLORS = {
    "gold": "#E8C84A",
    "green": "#2EA043",
    "red": "#F85149",
    "gray": "#8B949E",
    "bg": "#0D1117",
    "card": "#161B22",
}


# ─────────────────────────────────────────
# CARGAR DATOS
# ─────────────────────────────────────────
@st.cache_data(ttl=300)
def load_correlations():
    try:
        return requests.get(f"{API_URL}/correlations", timeout=5).json()
    except Exception:
        return []

@st.cache_data(ttl=300)
def load_significant():
    try:
        return requests.get(f"{API_URL}/correlations/significant", timeout=5).json()
    except Exception:
        return []

@st.cache_data(ttl=300)
def load_matches():
    try:
        return requests.get(f"{API_URL}/matches?status=FINISHED", timeout=5).json()
    except Exception:
        return []


correlations = load_correlations()
significant = load_significant()
matches = load_matches()

# ─────────────────────────────────────────
# EXPLICACIÓN DEL PROYECTO
# ─────────────────────────────────────────
with st.expander("ℹ️ ¿Cómo funciona este análisis?", expanded=False):
    st.markdown("""
    Este sistema analiza **correlaciones estadísticas** entre eventos deportivos
    del Mundial 2026 y métricas económicas en tiempo real.

    **¿Qué medimos?**
    - **GOAL → STOCK**: ¿Sube o baja la acción de un sponsor tras un gol?
    - **GOAL → TRENDS**: ¿Se disparan las búsquedas en Google tras un gol?
    - **GOAL → SENTIMENT**: ¿Cambia el tono de las noticias económicas tras un gol?

    **¿Cómo lo calculamos?**
    Para cada evento capturamos una **ventana de 30 minutos antes y después**,
    calculamos la media de la métrica en cada ventana y aplicamos un
    **t-test estadístico** para determinar si el cambio es significativo (p < 0.05).

    **Importante**: Los datos se acumulan con el tiempo. Cuantos más partidos
    y snapshots tengamos, más robustas serán las correlaciones.
    """)

st.divider()

# ─────────────────────────────────────────
# MÉTRICAS GLOBALES
# ─────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    total = sum(c.get("total", 0) for c in correlations) if correlations else 0
    st.metric("🔬 Correlaciones calculadas", total)
with col2:
    sig = len(significant) if significant else 0
    st.metric("✅ Estadísticamente significativas", sig)
with col3:
    st.metric("⚽ Partidos analizados", len(matches))
with col4:
    pct = round((sig / total * 100), 1) if total > 0 else 0
    st.metric("📊 Tasa de significancia", f"{pct}%")

st.divider()

# ─────────────────────────────────────────
# GRÁFICO DE RESUMEN POR TIPO
# ─────────────────────────────────────────
st.markdown("### 📊 Delta medio por tipo de correlación")

if correlations:
    df_corr = pd.DataFrame(correlations)

    colors_bar = [COLORS["green"] if d > 0 else COLORS["red"]
                  for d in df_corr["avg_delta_pct"]]

    fig = go.Figure(go.Bar(
        x=df_corr["type"].str.replace("_", " → "),
        y=df_corr["avg_delta_pct"],
        marker_color=colors_bar,
        text=[f"{d:+.2f}%" for d in df_corr["avg_delta_pct"]],
        textposition="outside",
        width=0.4,
    ))
    fig.add_hline(y=0, line_color="#30363D", line_width=1)
    fig.update_layout(
        plot_bgcolor=COLORS["bg"],
        paper_bgcolor=COLORS["card"],
        font_color=COLORS["gray"],
        xaxis=dict(gridcolor="#30363D"),
        yaxis=dict(gridcolor="#30363D", ticksuffix="%"),
        margin=dict(t=40, b=20),
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabla de resumen
    st.markdown("#### Detalle por tipo")
    for c in correlations:
        corr_type = c["type"].replace("_", " → ")
        total_c = c["total"]
        sig_c = c["significant"]
        delta = c["avg_delta_pct"]
        max_d = c["max_delta_pct"]
        min_d = c["min_delta_pct"]
        color = COLORS["green"] if delta > 0 else COLORS["red"]

        st.markdown(f"""
        <div style="
            background: {COLORS['card']};
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 12px 16px;
            margin: 6px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 16px; font-weight: bold;">{corr_type}</span>
                    <div style="font-size: 12px; color: {COLORS['gray']}; margin-top: 4px;">
                        {total_c} correlaciones · {sig_c} significativas
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="color: {color}; font-size: 20px; font-weight: bold;">
                        {delta:+.2f}%
                    </div>
                    <div style="font-size: 11px; color: {COLORS['gray']};">
                        min: {min_d:+.2f}% · max: {max_d:+.2f}%
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.info("""
    ⏳ **Sin correlaciones calculadas todavía.**

    Las correlaciones se calculan automáticamente cuando hay:
    - Eventos de partido (goles, tarjetas) en la BD
    - Snapshots de stocks capturados durante esos eventos
    - Datos de tendencias y sentimiento en las ventanas temporales

    El sistema acumulará datos con cada partido del torneo.
    Vuelve durante un partido en vivo para ver los primeros resultados.
    """)

st.divider()

# ─────────────────────────────────────────
# CORRELACIONES SIGNIFICATIVAS
# ─────────────────────────────────────────
st.markdown("### ✅ Hallazgos significativos")

if significant:
    for c in significant:
        delta = c.get("delta_pct", 0)
        color = COLORS["green"] if delta > 0 else COLORS["red"]
        corr_type = c.get("correlation_type", "").replace("_", " → ")
        p_value = c.get("p_value", 1)

        st.markdown(f"""
        <div style="
            background: {COLORS['card']};
            border: 1px solid {color};
            border-radius: 10px;
            padding: 16px;
            margin: 8px 0;
        ">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <span style="color: {COLORS['gold']}; font-weight: bold;">
                        {corr_type}
                    </span>
                    <div style="font-size: 12px; color: {COLORS['gray']}; margin-top: 4px;">
                        p-value: {p_value:.4f} · Estadísticamente significativo ✅
                    </div>
                    <div style="font-size: 12px; color: {COLORS['gray']};">
                        Antes: {c.get('metric_before', 0):.4f} →
                        Después: {c.get('metric_after', 0):.4f}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="color: {color}; font-size: 28px; font-weight: bold;">
                        {delta:+.2f}%
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("""
    🔍 **Aún no hay hallazgos significativos.**

    Esto es normal al inicio del torneo. A medida que el sistema
    acumule datos de partidos en vivo, aparecerán aquí las
    correlaciones estadísticamente probadas.
    """)

st.divider()

# ─────────────────────────────────────────
# CONTEXTO EDUCATIVO
# ─────────────────────────────────────────
st.markdown("### 📚 ¿Qué estamos buscando?")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div style="background: {COLORS['card']}; border-radius: 10px; padding: 16px;">
        <div style="font-size: 20px;">📈</div>
        <div style="font-weight: bold; margin: 8px 0;">Gol → Bolsa</div>
        <div style="font-size: 13px; color: {COLORS['gray']};">
            ¿Sube la acción de Nike cuando marca un equipo que viste Nike?
            ¿Reacciona Adidas a los goles de equipos patrocinados?
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background: {COLORS['card']}; border-radius: 10px; padding: 16px;">
        <div style="font-size: 20px;">🔍</div>
        <div style="font-weight: bold; margin: 8px 0;">Gol → Búsquedas</div>
        <div style="font-size: 13px; color: {COLORS['gray']};">
            ¿Se disparan las búsquedas de "ver Mundial" o "streaming fútbol"
            tras un gol importante?
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background: {COLORS['card']}; border-radius: 10px; padding: 16px;">
        <div style="font-size: 20px;">📰</div>
        <div style="font-weight: bold; margin: 8px 0;">Gol → Sentimiento</div>
        <div style="font-size: 13px; color: {COLORS['gray']};">
            ¿Cambia el tono de las noticias económicas tras una eliminación
            o una victoria sorpresa?
        </div>
    </div>
    """, unsafe_allow_html=True)