import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


COLORS = {
    "gold": "#E8C84A",
    "green": "#2EA043",
    "red": "#F85149",
    "gray": "#8B949E",
    "bg": "#0D1117",
    "card": "#161B22",
}


def standings_chart(table: list[dict], group_name: str) -> go.Figure:
    """Gráfico de barras de clasificación de un grupo"""
    df = pd.DataFrame(table)
    fig = px.bar(
        df,
        x="team",
        y="points",
        color="points",
        color_continuous_scale=["#30363D", COLORS["gold"]],
        title=f"Clasificación — {group_name}",
        labels={"team": "Equipo", "points": "Puntos"},
    )
    fig.update_layout(
        plot_bgcolor=COLORS["bg"],
        paper_bgcolor=COLORS["bg"],
        font_color=COLORS["gray"],
        showlegend=False,
        coloraxis_showscale=False,
    )
    return fig


def stock_history_chart(history: list[dict], ticker: str) -> go.Figure:
    """Gráfico de línea del histórico de un sponsor"""
    if not history:
        return go.Figure()

    df = pd.DataFrame(history)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp_utc"],
        y=df["price"],
        mode="lines",
        line=dict(color=COLORS["gold"], width=2),
        name=ticker,
        fill="tozeroy",
        fillcolor="rgba(232, 200, 74, 0.1)",
    ))
    fig.update_layout(
        title=f"{ticker} — Evolución del precio",
        plot_bgcolor=COLORS["bg"],
        paper_bgcolor=COLORS["bg"],
        font_color=COLORS["gray"],
        xaxis=dict(gridcolor="#30363D"),
        yaxis=dict(gridcolor="#30363D"),
    )
    return fig


def sentiment_gauge(score: float, title: str) -> go.Figure:
    """Gauge de sentimiento (-1 a 1)"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title, "font": {"color": COLORS["gray"]}},
        gauge={
            "axis": {"range": [-1, 1], "tickcolor": COLORS["gray"]},
            "bar": {"color": COLORS["gold"]},
            "steps": [
                {"range": [-1, -0.1], "color": "#F85149"},
                {"range": [-0.1, 0.1], "color": "#30363D"},
                {"range": [0.1, 1], "color": "#2EA043"},
            ],
        },
        number={"font": {"color": "white"}},
    ))
    fig.update_layout(
        paper_bgcolor=COLORS["bg"],
        font_color=COLORS["gray"],
        height=250,
    )
    return fig


def correlation_chart(correlations: list[dict]) -> go.Figure:
    """Gráfico de correlaciones por tipo"""
    if not correlations:
        return go.Figure()

    df = pd.DataFrame(correlations)
    colors = [COLORS["green"] if d > 0 else COLORS["red"]
              for d in df["avg_delta_pct"]]

    fig = go.Figure(go.Bar(
        x=df["type"],
        y=df["avg_delta_pct"],
        marker_color=colors,
        text=[f"{d:+.2f}%" for d in df["avg_delta_pct"]],
        textposition="outside",
    ))
    fig.update_layout(
        title="Delta medio por tipo de correlación (%)",
        plot_bgcolor=COLORS["bg"],
        paper_bgcolor=COLORS["bg"],
        font_color=COLORS["gray"],
        xaxis=dict(gridcolor="#30363D"),
        yaxis=dict(gridcolor="#30363D"),
    )
    return fig