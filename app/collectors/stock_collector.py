import yfinance as yf
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logger import logger

# Mapa de tickers con metadata de cada sponsor
SPONSORS_METADATA = {
    "ADDYY": {
        "company_name": "Adidas",
        "sponsor_country": "Germany",
        "category": "Equipment"
    },
    "NKE": {
        "company_name": "Nike",
        "sponsor_country": "USA",
        "category": "Equipment"
    },
    "KO": {
        "company_name": "Coca-Cola",
        "sponsor_country": "USA",
        "category": "Beverages"
    },
    "BUD": {
        "company_name": "Anheuser-Busch InBev",
        "sponsor_country": "Belgium",
        "category": "Beverages"
    },
    "V": {
        "company_name": "Visa",
        "sponsor_country": "USA",
        "category": "Payments"
    },
    "BABA": {
        "company_name": "Alibaba",
        "sponsor_country": "China",
        "category": "Technology"
    },
    "FOX": {
        "company_name": "Fox Corporation",
        "sponsor_country": "USA",
        "category": "Media"
    },
}


def get_current_snapshot(ticker: str) -> dict | None:
    """
    Obtiene el precio actual y métricas básicas de un ticker.
    Usado durante partidos en vivo para capturar snapshots cada 5 min.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info

        price = info.last_price
        prev_close = info.previous_close

        if not price or not prev_close:
            logger.warning(f"No hay datos de precio para {ticker}")
            return None

        change_pct = ((price - prev_close) / prev_close) * 100
        metadata = SPONSORS_METADATA.get(ticker, {})

        snapshot = {
            "ticker": ticker,
            "company_name": metadata.get("company_name", ticker),
            "sponsor_country": metadata.get("sponsor_country"),
            "price": round(price, 4),
            "volume": info.three_month_average_volume,
            "change_pct": round(change_pct, 4),
            "timestamp_utc": datetime.now(timezone.utc),
        }

        logger.info(f"{ticker} ({metadata.get('company_name')}) → ${price:.2f} ({change_pct:+.2f}%)")
        return snapshot

    except Exception as e:
        logger.error(f"Error obteniendo snapshot de {ticker}: {e}")
        return None


def get_all_snapshots() -> list[dict]:
    """
    Obtiene snapshots de todos los sponsors configurados.
    Retorna solo los que han tenido éxito.
    """
    snapshots = []
    tickers = settings.tickers_list

    logger.info(f"Capturando snapshots de {len(tickers)} tickers...")

    for ticker in tickers:
        snapshot = get_current_snapshot(ticker)
        if snapshot:
            snapshots.append(snapshot)

    logger.info(f"Snapshots obtenidos: {len(snapshots)}/{len(tickers)}")
    return snapshots


def get_historical_data(ticker: str, period: str = "1mo") -> list[dict]:
    """
    Obtiene histórico de un ticker para análisis de correlaciones.
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval="5m")

        if hist.empty:
            logger.warning(f"Sin datos históricos para {ticker}")
            return []

        records = []
        for timestamp, row in hist.iterrows():
            records.append({
                "ticker": ticker,
                "price": round(row["Close"], 4),
                "volume": row["Volume"],
                "timestamp_utc": timestamp.to_pydatetime(),
            })

        logger.info(f"Histórico {ticker}: {len(records)} registros ({period})")
        return records

    except Exception as e:
        logger.error(f"Error obteniendo histórico de {ticker}: {e}")
        return []