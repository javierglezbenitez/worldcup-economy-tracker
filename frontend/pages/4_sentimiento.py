import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json

import streamlit as st
API_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Sentimiento — World Cup Economy Tracker",
    page_icon="📰",
    layout="wide",
)

st.markdown("# 📰 Sentimiento Económico")
st.markdown("Análisis de sentimiento de noticias económicas relacionadas con el Mundial 2026")
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
def load_summary():
    try:
        return requests.get(f"{API_URL}/sentiment/summary", timeout=5).json()
    except Exception:
        return []

@st.cache_data(ttl=300)
def load_news():
    try:
        return requests.get(f"{API_URL}/sentiment", timeout=5).json()
    except Exception:
        return []

@st.cache_data(ttl=300)
def load_entities():
    try:
        return requests.get(f"{API_URL}/sentiment/entities", timeout=5).json()
    except Exception:
        return []


summary = load_summary()
news = load_news()
entities = load_entities()

# ─────────────────────────────────────────
# RESUMEN DE SENTIMIENTO POR CATEGORÍA
# ─────────────────────────────────────────
st.markdown("### 🌡️ Pulso económico por categoría")

if summary:
    cols = st.columns(len(summary))
    for i, s in enumerate(summary):
        with cols[i]:
            icon = "🟢" if s["sentiment_label"] == "POSITIVE" else "🔴" if s["sentiment_label"] == "NEGATIVE" else "⚪"
            color = COLORS["green"] if s["sentiment_label"] == "POSITIVE" else COLORS["red"] if s["sentiment_label"] == "NEGATIVE" else COLORS["gray"]

            st.markdown(f"""
            <div style="
                background: {COLORS['card']};
                border: 2px solid {color};
                border-radius: 12px;
                padding: 20px;
                text-align: center;
            ">
                <div style="font-size: 11px; color: {COLORS['gray']}; margin-bottom: 8px;">
                    {s['category']}
                </div>
                <div style="font-size: 36px;">{icon}</div>
                <div style="color: {color}; font-weight: bold; font-size: 16px; margin: 8px 0;">
                    {s['sentiment_label']}
                </div>
                <div style="font-size: 24px; font-weight: bold; color: white;">
                    {s['avg_sentiment']:+.3f}
                </div>
                <div style="font-size: 12px; color: {COLORS['gray']}; margin-top: 8px;">
                    📰 {s['total_articles']} artículos<br>
                    🟢 {s['positive']} pos &nbsp; ⚪ {s['neutral']} neu &nbsp; 🔴 {s['negative']} neg
                </div>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────
# GRÁFICOS
# ─────────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📊 Sentimiento medio por categoría")
    if summary:
        df_sum = pd.DataFrame(summary)
        colors_bar = [COLORS["green"] if s > 0 else COLORS["red"]
                      for s in df_sum["avg_sentiment"]]

        fig = go.Figure(go.Bar(
            x=df_sum["category"],
            y=df_sum["avg_sentiment"],
            marker_color=colors_bar,
            text=[f"{s:+.3f}" for s in df_sum["avg_sentiment"]],
            textposition="outside",
        ))
        fig.add_hline(y=0, line_color="#30363D", line_width=1)
        fig.update_layout(
            plot_bgcolor=COLORS["bg"],
            paper_bgcolor=COLORS["card"],
            font_color=COLORS["gray"],
            yaxis=dict(gridcolor="#30363D", range=[-1, 1]),
            xaxis=dict(gridcolor="#30363D"),
            margin=dict(t=20, b=20),
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 🏷️ Entidades más mencionadas")
    if entities:
        df_ent = pd.DataFrame(entities)
        fig_ent = px.bar(
            df_ent,
            x="mentions",
            y="entity",
            orientation="h",
            color="mentions",
            color_continuous_scale=["#30363D", COLORS["gold"]],
        )
        fig_ent.update_layout(
            plot_bgcolor=COLORS["bg"],
            paper_bgcolor=COLORS["card"],
            font_color=COLORS["gray"],
            coloraxis_showscale=False,
            margin=dict(t=20, b=20),
            height=300,
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_ent, use_container_width=True)

st.divider()

# ─────────────────────────────────────────
# NOTICIAS RECIENTES
# ─────────────────────────────────────────
st.markdown("### 📋 Noticias recientes")

# Filtros
col1, col2 = st.columns([2, 1])
with col1:
    categories = ["Todas"] + list(set(n.get("category", "") for n in news if n.get("category")))
    selected_cat = st.selectbox("Filtrar por categoría", categories)
with col2:
    sentiment_filter = st.selectbox(
        "Filtrar por sentimiento",
        ["Todos", "Positivo 🟢", "Neutro ⚪", "Negativo 🔴"]
    )

# Aplicar filtros
filtered_news = news
if selected_cat != "Todas":
    filtered_news = [n for n in filtered_news if n.get("category") == selected_cat]
if sentiment_filter == "Positivo 🟢":
    filtered_news = [n for n in filtered_news if n.get("sentiment_score", 0) > 0.1]
elif sentiment_filter == "Negativo 🔴":
    filtered_news = [n for n in filtered_news if n.get("sentiment_score", 0) < -0.1]
elif sentiment_filter == "Neutro ⚪":
    filtered_news = [n for n in filtered_news
                     if -0.1 <= n.get("sentiment_score", 0) <= 0.1]

st.markdown(f"Mostrando **{len(filtered_news)}** noticias")

for article in filtered_news:
    score = article.get("sentiment_score", 0)
    color = COLORS["green"] if score > 0.1 else COLORS["red"] if score < -0.1 else COLORS["gray"]
    icon = "🟢" if score > 0.1 else "🔴" if score < -0.1 else "⚪"
    category = article.get("category", "")
    source = article.get("source", "")
    url = article.get("url", "")

    try:
        entities_list = json.loads(article.get("entities", "[]"))
        entities_str = " · ".join(entities_list) if entities_list else "—"
    except Exception:
        entities_str = "—"

    # Titular con o sin enlace
    if url:
        headline_html = (
            f'<a href="{url}" target="_blank" style="'
            f'color: white; text-decoration: none; font-size: 15px; font-weight: bold;">'
            f'{article.get("headline", "")[:100]} 🔗</a>'
        )
    else:
        headline_html = (
            f'<span style="font-size: 15px; font-weight: bold;">'
            f'{article.get("headline", "")[:100]}</span>'
        )

    st.markdown(f"""
    <div style="
        background: {COLORS['card']};
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 12px 16px;
        margin: 6px 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="flex: 1;">
                {headline_html}
                <div style="margin-top: 6px; font-size: 12px; color: {COLORS['gray']};">
                    📌 {source} &nbsp;|&nbsp; 🏷️ {category} &nbsp;|&nbsp; 🔗 {entities_str}
                </div>
            </div>
            <div style="text-align: center; margin-left: 16px; min-width: 60px;">
                <div style="font-size: 20px;">{icon}</div>
                <div style="color: {color}; font-size: 13px; font-weight: bold;">
                    {score:+.2f}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)