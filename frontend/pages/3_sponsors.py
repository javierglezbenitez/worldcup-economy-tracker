import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

import streamlit as st
API_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Sponsors — World Cup Economy Tracker",
    page_icon="📈",
    layout="wide",
)

st.markdown("# 📈 Sponsors & Mercados")
st.markdown("Cotizaciones en tiempo real de los grandes sponsors del Mundial 2026")
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
@st.cache_data(ttl=60)
def load_snapshots():
    try:
        return requests.get(f"{API_URL}/stocks/snapshots", timeout=5).json()
    except Exception:
        return []

@st.cache_data(ttl=300)
def load_history(ticker: str, hours: int = 24):
    try:
        return requests.get(
            f"{API_URL}/stocks/{ticker}/history?hours={hours}",
            timeout=5
        ).json()
    except Exception:
        return []


snapshots = load_snapshots()

if not snapshots:
    st.error("No se pudieron cargar los datos de sponsors")
    st.stop()

# ─────────────────────────────────────────
# MÉTRICAS GLOBALES
# ─────────────────────────────────────────
up = sum(1 for s in snapshots if s["trend"] == "UP")
down = sum(1 for s in snapshots if s["trend"] == "DOWN")
neutral = sum(1 for s in snapshots if s["trend"] == "NEUTRAL")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📊 Sponsors tracked", len(snapshots))
with col2:
    st.metric("📈 Al alza", up, delta=f"+{up}")
with col3:
    st.metric("📉 A la baja", down, delta=f"-{down}", delta_color="inverse")
with col4:
    avg_change = sum(s["change_pct"] for s in snapshots) / len(snapshots)
    st.metric("📊 Cambio medio", f"{avg_change:+.2f}%",
              delta_color="normal" if avg_change >= 0 else "inverse")

st.divider()

# ─────────────────────────────────────────
# GRID DE SPONSORS
# ─────────────────────────────────────────
st.markdown("### 💼 Sponsors en tiempo real")

cols = st.columns(4)
for i, stock in enumerate(snapshots):
    with cols[i % 4]:
        trend = stock["trend"]
        color = COLORS["green"] if trend == "UP" else COLORS["red"] if trend == "DOWN" else COLORS["gray"]
        arrow = "▲" if trend == "UP" else "▼" if trend == "DOWN" else "●"
        border = f"2px solid {color}"

        st.markdown(f"""
        <div style="
            background: {COLORS['card']};
            border: {border};
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            margin-bottom: 12px;
        ">
            <div style="color: {COLORS['gray']}; font-size: 12px;">{stock['ticker']}</div>
            <div style="font-size: 15px; font-weight: bold; margin: 4px 0;">
                {stock['company_name']}
            </div>
            <div style="font-size: 26px; font-weight: bold; color: white;">
                ${stock['price']:.2f}
            </div>
            <div style="color: {color}; font-size: 16px; font-weight: bold;">
                {arrow} {stock['change_pct']:+.2f}%
            </div>
            <div style="color: {COLORS['gray']}; font-size: 11px; margin-top: 4px;">
                {stock.get('sponsor_country', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────
# GRÁFICO COMPARATIVO
# ─────────────────────────────────────────
st.markdown("### 📊 Comparativa de rendimiento")

df_snap = pd.DataFrame(snapshots)
colors_bar = [COLORS["green"] if c > 0 else COLORS["red"]
              for c in df_snap["change_pct"]]

fig_compare = go.Figure(go.Bar(
    x=df_snap["company_name"],
    y=df_snap["change_pct"],
    marker_color=colors_bar,
    text=[f"{c:+.2f}%" for c in df_snap["change_pct"]],
    textposition="outside",
))
fig_compare.update_layout(
    title="Cambio % hoy de cada sponsor",
    plot_bgcolor=COLORS["bg"],
    paper_bgcolor=COLORS["card"],
    font_color=COLORS["gray"],
    xaxis=dict(gridcolor="#30363D"),
    yaxis=dict(gridcolor="#30363D", ticksuffix="%"),
    margin=dict(t=40, b=20),
)
fig_compare.add_hline(y=0, line_color="#30363D", line_width=1)
st.plotly_chart(fig_compare, use_container_width=True)

st.divider()

# ─────────────────────────────────────────
# HISTÓRICO INDIVIDUAL
# ─────────────────────────────────────────
st.markdown("### 🔍 Histórico de un sponsor")

col1, col2 = st.columns([2, 1])
with col1:
    ticker_options = {s["company_name"]: s["ticker"] for s in snapshots}
    selected_company = st.selectbox("Selecciona un sponsor", list(ticker_options.keys()))
    selected_ticker = ticker_options[selected_company]
with col2:
    hours = st.selectbox("Periodo", [6, 12, 24, 48, 72], index=2,
                         format_func=lambda x: f"Últimas {x}h")

history = load_history(selected_ticker, hours)

if not history or len(history) < 2:
    st.info(
        f"📊 Solo hay {len(history)} snapshot(s) registrado(s) para {selected_company} todavía. "
        f"El histórico se construye automáticamente cada 30 minutos (cada 5 min durante partidos en vivo). "
        f"Vuelve más tarde para ver la evolución completa."
    )
else:
    df_hist = pd.DataFrame(history)
    df_hist["timestamp_utc"] = pd.to_datetime(df_hist["timestamp_utc"])

    first_price = df_hist["price"].iloc[0]
    last_price = df_hist["price"].iloc[-1]
    delta = ((last_price - first_price) / first_price) * 100
    line_color = COLORS["green"] if delta >= 0 else COLORS["red"]

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(
        x=df_hist["timestamp_utc"],
        y=df_hist["price"],
        mode="lines+markers",
        line=dict(color=line_color, width=2),
        marker=dict(size=5),
        name=selected_ticker,
        fill="tozeroy",
        fillcolor=f"rgba({int(line_color[1:3], 16)}, "
                  f"{int(line_color[3:5], 16)}, "
                  f"{int(line_color[5:7], 16)}, 0.1)",
    ))
    fig_hist.update_layout(
        title=f"{selected_company} ({selected_ticker}) — Últimas {hours}h",
        plot_bgcolor=COLORS["bg"],
        paper_bgcolor=COLORS["card"],
        font_color=COLORS["gray"],
        xaxis=dict(gridcolor="#30363D"),
        yaxis=dict(gridcolor="#30363D", tickprefix="$"),
        margin=dict(t=40, b=20),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Precio inicial", f"${first_price:.2f}")
    with col2:
        st.metric("Precio actual", f"${last_price:.2f}")
    with col3:
        st.metric("Variación periodo", f"{delta:+.2f}%",
                  delta_color="normal" if delta >= 0 else "inverse")