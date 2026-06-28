from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from scipy import stats
import numpy as np
from app.models.database import Correlation, MatchEvent, StockSnapshot, SearchTrend, NewsSentiment
from app.core.logger import logger


def calculate_goal_to_stock_correlation(
    db: Session,
    event: MatchEvent,
    ticker: str,
    window_minutes: int = 30
) -> dict | None:
    """
    Calcula si un gol tuvo impacto estadístico en el precio de un sponsor.
    Compara el precio medio PRE-evento vs POST-evento.
    """
    window = timedelta(minutes=window_minutes)
    event_ts = event.timestamp_utc

    # Precios ANTES del evento
    prices_before = db.query(StockSnapshot.price).filter(
        StockSnapshot.ticker == ticker,
        StockSnapshot.timestamp_utc >= event_ts - window,
        StockSnapshot.timestamp_utc < event_ts
    ).all()

    # Precios DESPUÉS del evento
    prices_after = db.query(StockSnapshot.price).filter(
        StockSnapshot.ticker == ticker,
        StockSnapshot.timestamp_utc > event_ts,
        StockSnapshot.timestamp_utc <= event_ts + window
    ).all()

    if len(prices_before) < 2 or len(prices_after) < 2:
        logger.debug(f"Datos insuficientes para correlación {ticker} en evento {event.id}")
        return None

    before_values = [p[0] for p in prices_before]
    after_values = [p[0] for p in prices_after]

    mean_before = np.mean(before_values)
    mean_after = np.mean(after_values)
    delta_pct = ((mean_after - mean_before) / mean_before) * 100

    # T-test para ver si el cambio es estadísticamente significativo
    t_stat, p_value = stats.ttest_ind(before_values, after_values)

    result = {
        "event_id": event.id,
        "match_id": event.match_id,
        "correlation_type": "GOAL_TO_STOCK",
        "metric_before": round(float(mean_before), 4),
        "metric_after": round(float(mean_after), 4),
        "delta_pct": round(float(delta_pct), 4),
        "correlation_score": round(float(abs(delta_pct) / 100), 4),
        "p_value": round(float(p_value), 6),
        "is_significant": bool(p_value < 0.05),
    }

    logger.info(
        f"Correlación GOAL→{ticker}: delta={delta_pct:+.2f}% "
        f"p={p_value:.4f} {'✅ significativa' if p_value < 0.05 else '❌ no significativa'}"
    )
    return result


def calculate_goal_to_trends_correlation(
    db: Session,
    event: MatchEvent,
    window_minutes: int = 30
) -> dict | None:
    """
    Calcula si un gol provocó un pico en las búsquedas de Google.
    """
    window = timedelta(minutes=window_minutes)
    event_ts = event.timestamp_utc

    scores_before = db.query(SearchTrend.interest_score).filter(
        SearchTrend.timestamp_utc >= event_ts - window,
        SearchTrend.timestamp_utc < event_ts
    ).all()

    scores_after = db.query(SearchTrend.interest_score).filter(
        SearchTrend.timestamp_utc > event_ts,
        SearchTrend.timestamp_utc <= event_ts + window
    ).all()

    if len(scores_before) < 2 or len(scores_after) < 2:
        logger.debug(f"Datos insuficientes para correlación trends en evento {event.id}")
        return None

    before_values = [s[0] for s in scores_before]
    after_values = [s[0] for s in scores_after]

    mean_before = np.mean(before_values)
    mean_after = np.mean(after_values)

    if mean_before == 0:
        return None

    delta_pct = ((mean_after - mean_before) / mean_before) * 100
    t_stat, p_value = stats.ttest_ind(before_values, after_values)

    result = {
        "event_id": event.id,
        "match_id": event.match_id,
        "correlation_type": "GOAL_TO_TRENDS",
        "metric_before": round(float(mean_before), 4),
        "metric_after": round(float(mean_after), 4),
        "delta_pct": round(float(delta_pct), 4),
        "correlation_score": round(float(abs(delta_pct) / 100), 4),
        "p_value": round(float(p_value), 6),
        "is_significant": bool(p_value < 0.05),
    }

    logger.info(
        f"Correlación GOAL→TRENDS: delta={delta_pct:+.2f}% "
        f"p={p_value:.4f} {'✅ significativa' if p_value < 0.05 else '❌ no significativa'}"
    )
    return result


def calculate_goal_to_sentiment_correlation(
    db: Session,
    event: MatchEvent,
    window_minutes: int = 60
) -> dict | None:
    """
    Calcula si un gol impactó en el sentimiento de las noticias económicas.
    Usa ventana más amplia (60 min) porque las noticias tardan más en publicarse.
    """
    window = timedelta(minutes=window_minutes)
    event_ts = event.timestamp_utc

    sentiments_before = db.query(NewsSentiment.sentiment_score).filter(
        NewsSentiment.timestamp_utc >= event_ts - window,
        NewsSentiment.timestamp_utc < event_ts
    ).all()

    sentiments_after = db.query(NewsSentiment.sentiment_score).filter(
        NewsSentiment.timestamp_utc > event_ts,
        NewsSentiment.timestamp_utc <= event_ts + window
    ).all()

    if len(sentiments_before) < 2 or len(sentiments_after) < 2:
        logger.debug(f"Datos insuficientes para correlación sentimiento en evento {event.id}")
        return None

    before_values = [s[0] for s in sentiments_before]
    after_values = [s[0] for s in sentiments_after]

    mean_before = np.mean(before_values)
    mean_after = np.mean(after_values)
    delta_pct = ((mean_after - mean_before) / abs(mean_before)) * 100 if mean_before != 0 else 0
    t_stat, p_value = stats.ttest_ind(before_values, after_values)

    result = {
        "event_id": event.id,
        "match_id": event.match_id,
        "correlation_type": "GOAL_TO_SENTIMENT",
        "metric_before": round(float(mean_before), 4),
        "metric_after": round(float(mean_after), 4),
        "delta_pct": round(float(delta_pct), 4),
        "correlation_score": round(float(abs(delta_pct) / 100), 4),
        "p_value": round(float(p_value), 6),
        "is_significant": bool(p_value < 0.05),
    }

    logger.info(
        f"Correlación GOAL→SENTIMENT: delta={delta_pct:+.2f}% "
        f"p={p_value:.4f} {'✅ significativa' if p_value < 0.05 else '❌ no significativa'}"
    )
    return result


def run_all_correlations(db: Session) -> int:
    """
    Ejecuta todos los análisis de correlación para eventos
    que aún no han sido procesados.
    Retorna el número de correlaciones calculadas.
    """
    from app.core.config import settings

    # Obtener eventos sin correlaciones calculadas
    processed_event_ids = db.query(Correlation.event_id).distinct().all()
    processed_ids = {e[0] for e in processed_event_ids}

    events = db.query(MatchEvent).filter(
        MatchEvent.event_type.in_(["GOAL", "RED_CARD"])
    ).all()

    unprocessed = [e for e in events if e.id not in processed_ids]
    logger.info(f"Eventos pendientes de correlación: {len(unprocessed)}")

    count = 0
    for event in unprocessed:
        # Correlación con cada ticker de sponsor
        for ticker in settings.tickers_list:
            result = calculate_goal_to_stock_correlation(db, event, ticker)
            if result:
                correlation = Correlation(**result)
                db.add(correlation)
                count += 1

        # Correlación con Google Trends
        result = calculate_goal_to_trends_correlation(db, event)
        if result:
            correlation = Correlation(**result)
            db.add(correlation)
            count += 1

        # Correlación con sentimiento de noticias
        result = calculate_goal_to_sentiment_correlation(db, event)
        if result:
            correlation = Correlation(**result)
            db.add(correlation)
            count += 1

    db.commit()
    logger.info(f"Correlaciones calculadas y guardadas: {count}")
    return count


def get_significant_correlations(db: Session) -> list[Correlation]:
    """Obtiene solo las correlaciones estadísticamente significativas"""
    return db.query(Correlation).filter(
        Correlation.is_significant == True
    ).order_by(Correlation.delta_pct.desc()).all()


def get_correlations_summary(db: Session) -> list[dict]:
    """
    Resumen de correlaciones agrupadas por tipo.
    Muestra el delta medio y cuántas son significativas.
    """
    types = ["GOAL_TO_STOCK", "GOAL_TO_TRENDS", "GOAL_TO_SENTIMENT"]
    summary = []

    for corr_type in types:
        correlations = db.query(Correlation).filter(
            Correlation.correlation_type == corr_type
        ).all()

        if not correlations:
            continue

        deltas = [c.delta_pct for c in correlations if c.delta_pct is not None]
        significant = sum(1 for c in correlations if c.is_significant)

        summary.append({
            "type": corr_type,
            "total": len(correlations),
            "significant": significant,
            "avg_delta_pct": round(np.mean(deltas), 4) if deltas else 0,
            "max_delta_pct": round(max(deltas), 4) if deltas else 0,
            "min_delta_pct": round(min(deltas), 4) if deltas else 0,
        })

    return summary