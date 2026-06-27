from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from app.models.database import StockSnapshot, Match
from app.collectors.stock_collector import get_all_snapshots, get_current_snapshot
from app.core.logger import logger


def sync_stock_snapshots(db: Session, match_id: int = None) -> int:
    """
    Captura snapshots actuales de todos los sponsors y los guarda en BD.
    Si se pasa match_id, los asocia al partido en curso.
    Retorna el número de snapshots guardados.
    """
    snapshots = get_all_snapshots()
    if not snapshots:
        logger.warning("No se obtuvieron snapshots de stocks")
        return 0

    count = 0
    for snapshot_data in snapshots:
        snapshot = StockSnapshot(
            match_id=match_id,
            **snapshot_data
        )
        db.add(snapshot)
        count += 1

    db.commit()
    logger.info(f"Guardados {count} snapshots de stocks en BD")
    return count


def get_snapshots_during_match(db: Session, match_id: int) -> list[StockSnapshot]:
    """
    Obtiene todos los snapshots capturados durante un partido concreto.
    Útil para analizar cómo se movieron los stocks durante el juego.
    """
    return db.query(StockSnapshot).filter(
        StockSnapshot.match_id == match_id
    ).order_by(StockSnapshot.timestamp_utc).all()


def get_latest_snapshots(db: Session) -> list[dict]:
    """
    Obtiene el snapshot más reciente de cada ticker.
    Lo que se muestra en el dashboard como precio actual.
    """
    # Subconsulta: máximo timestamp por ticker
    subquery = db.query(
        StockSnapshot.ticker,
        func.max(StockSnapshot.timestamp_utc).label("max_ts")
    ).group_by(StockSnapshot.ticker).subquery()

    # Join para obtener el registro completo
    latest = db.query(StockSnapshot).join(
        subquery,
        (StockSnapshot.ticker == subquery.c.ticker) &
        (StockSnapshot.timestamp_utc == subquery.c.max_ts)
    ).all()

    results = []
    for s in latest:
        trend = "UP" if s.change_pct > 0.1 else "DOWN" if s.change_pct < -0.1 else "NEUTRAL"
        results.append({
            "ticker": s.ticker,
            "company_name": s.company_name,
            "sponsor_country": s.sponsor_country,
            "price": s.price,
            "change_pct": s.change_pct,
            "trend": trend,
            "timestamp_utc": s.timestamp_utc,
        })

    logger.info(f"Últimos snapshots obtenidos: {len(results)} tickers")
    return results


def get_stock_history(db: Session, ticker: str, hours: int = 24) -> list[StockSnapshot]:
    """
    Obtiene el histórico de un ticker en las últimas N horas.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    return db.query(StockSnapshot).filter(
        StockSnapshot.ticker == ticker,
        StockSnapshot.timestamp_utc >= since
    ).order_by(StockSnapshot.timestamp_utc).all()


def get_stock_delta_around_event(
    db: Session,
    ticker: str,
    event_timestamp: datetime,
    window_minutes: int = 30
) -> dict | None:
    """
    Calcula el delta de precio de un stock antes y después de un evento.
    Esto es el corazón del análisis de correlaciones.

    Retorna:
        price_before: precio medio en la ventana PRE-evento
        price_after: precio medio en la ventana POST-evento
        delta_pct: cambio porcentual
    """
    window = timedelta(minutes=window_minutes)

    # Precio medio ANTES del evento
    before = db.query(func.avg(StockSnapshot.price)).filter(
        StockSnapshot.ticker == ticker,
        StockSnapshot.timestamp_utc >= event_timestamp - window,
        StockSnapshot.timestamp_utc < event_timestamp
    ).scalar()

    # Precio medio DESPUÉS del evento
    after = db.query(func.avg(StockSnapshot.price)).filter(
        StockSnapshot.ticker == ticker,
        StockSnapshot.timestamp_utc > event_timestamp,
        StockSnapshot.timestamp_utc <= event_timestamp + window
    ).scalar()

    if not before or not after:
        logger.warning(f"Sin datos suficientes para calcular delta de {ticker}")
        return None

    delta_pct = ((after - before) / before) * 100

    result = {
        "ticker": ticker,
        "event_timestamp": event_timestamp,
        "price_before": round(before, 4),
        "price_after": round(after, 4),
        "delta_pct": round(delta_pct, 4),
        "window_minutes": window_minutes,
    }

    logger.info(f"Delta {ticker} around event: {delta_pct:+.2f}%")
    return result