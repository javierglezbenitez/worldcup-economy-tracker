import streamlit as st


def match_card(home_team: str, away_team: str,
               home_score: int, away_score: int,
               stage: str, status: str):
    """Tarjeta visual de un partido"""
    status_color = "🔴" if status == "LIVE" else "✅" if status == "FINISHED" else "🕐"

    st.markdown(f"""
    <div style="
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 16px;
        margin: 8px 0;
    ">
        <div style="color: #8B949E; font-size: 12px; margin-bottom: 8px;">
            {status_color} {stage.replace('_', ' ')} — {status}
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 18px; font-weight: bold; flex: 1;">{home_team}</div>
            <div style="font-size: 24px; font-weight: bold; color: #E8C84A; padding: 0 16px;">
                {home_score if home_score is not None else '-'} : {away_score if away_score is not None else '-'}
            </div>
            <div style="font-size: 18px; font-weight: bold; flex: 1; text-align: right;">{away_team}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def stock_card(ticker: str, company: str, price: float,
               change_pct: float, trend: str):
    """Tarjeta visual de un sponsor/stock"""
    color = "#2EA043" if trend == "UP" else "#F85149" if trend == "DOWN" else "#8B949E"
    arrow = "▲" if trend == "UP" else "▼" if trend == "DOWN" else "●"

    st.markdown(f"""
    <div style="
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    ">
        <div style="color: #8B949E; font-size: 12px;">{ticker}</div>
        <div style="font-size: 16px; font-weight: bold; margin: 4px 0;">{company}</div>
        <div style="font-size: 24px; font-weight: bold;">${price:.2f}</div>
        <div style="color: {color}; font-size: 16px;">{arrow} {change_pct:+.2f}%</div>
    </div>
    """, unsafe_allow_html=True)


def sentiment_card(category: str, label: str,
                   avg_score: float, total: int):
    """Tarjeta de sentimiento por categoría"""
    color = "#2EA043" if label == "POSITIVE" else "#F85149" if label == "NEGATIVE" else "#8B949E"
    icon = "🟢" if label == "POSITIVE" else "🔴" if label == "NEGATIVE" else "⚪"

    st.markdown(f"""
    <div style="
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    ">
        <div style="font-size: 12px; color: #8B949E;">{category}</div>
        <div style="font-size: 28px; margin: 8px 0;">{icon}</div>
        <div style="color: {color}; font-weight: bold;">{label}</div>
        <div style="font-size: 12px; color: #8B949E;">score: {avg_score:.2f} | {total} artículos</div>
    </div>
    """, unsafe_allow_html=True)