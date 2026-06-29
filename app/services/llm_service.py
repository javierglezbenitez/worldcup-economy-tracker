from groq import Groq
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logger import logger
from app.models.database import Match, MatchEvent, StockSnapshot, NewsSentiment, Correlation
import json


client = Groq(api_key=settings.GROQ_API_KEY)


def build_context(db: Session) -> str:
    """
    Construye el contexto con datos reales del Mundial
    que se inyectará al LLM antes de responder.
    """

    # Partidos recientes finalizados
    recent_matches = db.query(Match).filter(
        Match.status == "FINISHED"
    ).order_by(Match.kickoff_utc.desc()).limit(10).all()

    # Partidos en vivo
    live_matches = db.query(Match).filter(
        Match.status == "LIVE"
    ).all()

    # Próximos partidos
    upcoming_matches = db.query(Match).filter(
        Match.status == "TIMED"
    ).order_by(Match.kickoff_utc).limit(5).all()

    # Últimos precios de sponsors
    from app.services.stock_service import get_latest_snapshots
    stocks = get_latest_snapshots(db)

    # Sentimiento económico
    from app.services.news_service import get_sentiment_summary
    sentiment = get_sentiment_summary(db)

    # Correlaciones significativas
    significant = db.query(Correlation).filter(
        Correlation.is_significant == True
    ).limit(5).all()

    # Construir contexto como texto estructurado
    context = f"""
=== CONTEXTO ACTUAL DEL MUNDIAL 2026 ===
Fecha actual: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

--- PARTIDOS EN VIVO ---
{_format_matches(live_matches) if live_matches else "No hay partidos en vivo ahora mismo."}

--- ÚLTIMOS RESULTADOS ---
{_format_matches(recent_matches)}

--- PRÓXIMOS PARTIDOS ---
{_format_matches(upcoming_matches) if upcoming_matches else "Sin próximos partidos programados."}

--- COTIZACIONES DE SPONSORS ---
{_format_stocks(stocks)}

--- SENTIMIENTO ECONÓMICO ---
{_format_sentiment(sentiment)}

--- CORRELACIONES SIGNIFICATIVAS DETECTADAS ---
{_format_correlations(significant) if significant else "Aún no hay correlaciones estadísticamente significativas detectadas."}
"""
    return context


def _format_matches(matches: list) -> str:
    if not matches:
        return "Sin datos"
    lines = []
    for m in matches:
        score = f"{m.home_score}-{m.away_score}" if m.home_score is not None else "vs"
        lines.append(
            f"• {m.home_team} {score} {m.away_team} "
            f"({m.stage.replace('_', ' ') if m.stage else ''} "
            f"{m.group or ''}) [{m.status}]"
        )
    return "\n".join(lines)


def _format_stocks(stocks: list) -> str:
    if not stocks:
        return "Sin datos de stocks"
    lines = []
    for s in stocks:
        trend = "▲" if s["trend"] == "UP" else "▼" if s["trend"] == "DOWN" else "●"
        lines.append(
            f"• {s['company_name']} ({s['ticker']}): "
            f"${s['price']:.2f} {trend} {s['change_pct']:+.2f}%"
        )
    return "\n".join(lines)


def _format_sentiment(sentiment: list) -> str:
    if not sentiment:
        return "Sin datos de sentimiento"
    lines = []
    for s in sentiment:
        lines.append(
            f"• {s['category']}: {s['sentiment_label']} "
            f"(score: {s['avg_sentiment']:+.3f}, "
            f"{s['total_articles']} artículos)"
        )
    return "\n".join(lines)


def _format_correlations(correlations: list) -> str:
    if not correlations:
        return "Sin correlaciones significativas"
    lines = []
    for c in correlations:
        lines.append(
            f"• {c.correlation_type}: delta={c.delta_pct:+.2f}% "
            f"p-value={c.p_value:.4f}"
        )
    return "\n".join(lines)


def chat(
    db: Session,
    messages: list[dict],
    user_message: str
) -> str:
    """
    Genera una respuesta del agente con contexto real del Mundial.

    messages: historial de la conversación
    user_message: último mensaje del usuario
    """
    try:
        # Construir contexto con datos actuales
        context = build_context(db)

        # System prompt del agente
        system_prompt = f"""Eres un analista económico experto en el Mundial de Fútbol 2026.
Tu especialidad es descubrir y explicar las correlaciones ocultas entre los eventos 
deportivos y la economía: mercados financieros, publicidad, audiencias, sponsors y consumo.

Tienes acceso a datos en tiempo real del torneo. Responde siempre en español,
de forma clara, directa y con datos concretos cuando estén disponibles.

Si te preguntan sobre correlaciones o impacto económico, explica los mecanismos
detrás de los datos y sé honesto sobre las limitaciones del análisis.

Si no tienes datos suficientes para responder algo con precisión, dilo claramente
y explica qué datos se necesitarían.

{context}
"""

        # Construir mensajes para la API
        api_messages = [{"role": "system", "content": system_prompt}]

        # Añadir historial (últimos 10 mensajes para no exceder contexto)
        for msg in messages[-10:]:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Añadir mensaje actual del usuario
        api_messages.append({"role": "user", "content": user_message})

        # Llamar a Groq
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=api_messages,
            max_tokens=1000,
            temperature=0.7,
        )

        answer = response.choices[0].message.content
        logger.info(f"LLM respondió correctamente ({len(answer)} chars)")
        return answer

    except Exception as e:
        logger.error(f"Error en LLM service: {e}")
        return "Lo siento, ha ocurrido un error al procesar tu pregunta. Inténtalo de nuevo."