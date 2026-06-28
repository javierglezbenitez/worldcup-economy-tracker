from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from app.models.database import NewsSentiment, Match
from app.collectors.news_collector import get_all_news
from app.core.logger import logger
import json


def sync_news(db: Session, match_id: int = None) -> int:
    """
    Obtiene noticias económicas del Mundial y las guarda en BD.
    Evita duplicados por headline.
    Retorna el número de noticias nuevas guardadas.
    """
    articles = get_all_news()
    if not articles:
        logger.warning("No se obtuvieron noticias")
        return 0

    count = 0
    for article in articles:
        # Evitar duplicados por headline
        existing = db.query(NewsSentiment).filter(
            NewsSentiment.headline == article["headline"]
        ).first()

        if not existing:
            news = NewsSentiment(
                match_id=match_id,
                **article
            )
            db.add(news)
            count += 1

    db.commit()
    logger.info(f"Noticias nuevas guardadas: {count}")
    return count


def get_sentiment_summary(db: Session) -> list[dict]:
    """
    Calcula un resumen de sentimiento agrupado por categoría.
    Útil para el dashboard — muestra el pulso económico del Mundial.
    """
    categories = ["FINANCIAL", "ADVERTISING", "TOURISM", "STREAMING"]
    summaries = []

    for category in categories:
        articles = db.query(NewsSentiment).filter(
            NewsSentiment.category == category
        ).all()

        if not articles:
            continue

        total = len(articles)
        scores = [a.sentiment_score for a in articles]
        avg_sentiment = round(sum(scores) / total, 4)

        positive = sum(1 for s in scores if s > 0.1)
        negative = sum(1 for s in scores if s < -0.1)
        neutral = total - positive - negative

        if avg_sentiment > 0.1:
            label = "POSITIVE"
        elif avg_sentiment < -0.1:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"

        summaries.append({
            "category": category,
            "avg_sentiment": avg_sentiment,
            "total_articles": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "sentiment_label": label,
        })

    logger.info(f"Resumen de sentimiento calculado: {len(summaries)} categorías")
    return summaries


def get_latest_news(db: Session, category: str = None, limit: int = 10) -> list[NewsSentiment]:
    """
    Obtiene las noticias más recientes con filtro opcional por categoría.
    """
    query = db.query(NewsSentiment)
    if category:
        query = query.filter(NewsSentiment.category == category)
    return query.order_by(NewsSentiment.timestamp_utc.desc()).limit(limit).all()


def get_most_mentioned_entities(db: Session, limit: int = 10) -> list[dict]:
    """
    Analiza qué entidades económicas aparecen más en las noticias.
    Útil para ver qué sponsors o selecciones generan más cobertura.
    """
    articles = db.query(NewsSentiment).all()

    entity_count = {}
    for article in articles:
        if not article.entities:
            continue
        try:
            entities = json.loads(article.entities)
            for entity in entities:
                entity_count[entity] = entity_count.get(entity, 0) + 1
        except json.JSONDecodeError:
            continue

    # Ordenar por frecuencia
    sorted_entities = sorted(
        entity_count.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]

    result = [
        {"entity": entity, "mentions": count}
        for entity, count in sorted_entities
    ]

    logger.info(f"Entidades más mencionadas calculadas: {len(result)}")
    return result


def get_sentiment_trend(db: Session, hours: int = 24) -> list[dict]:
    """
    Obtiene la evolución del sentimiento en las últimas N horas.
    Permite ver cómo cambia el tono económico durante el torneo.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles = db.query(NewsSentiment).filter(
        NewsSentiment.timestamp_utc >= since
    ).order_by(NewsSentiment.timestamp_utc).all()

    if not articles:
        return []

    # Agrupar por hora
    hourly = {}
    for article in articles:
        hour_key = article.timestamp_utc.replace(
            minute=0, second=0, microsecond=0
        )
        if hour_key not in hourly:
            hourly[hour_key] = []
        hourly[hour_key].append(article.sentiment_score)

    trend = [
        {
            "hour": hour,
            "avg_sentiment": round(sum(scores) / len(scores), 4),
            "articles_count": len(scores),
        }
        for hour, scores in sorted(hourly.items())
    ]

    logger.info(f"Tendencia de sentimiento: {len(trend)} horas analizadas")
    return trend