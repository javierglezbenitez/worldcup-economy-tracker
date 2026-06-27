from pytrends.request import TrendReq
from datetime import datetime, timezone, timedelta
from app.core.logger import logger

# Keywords por selección — qué busca la gente cuando juega cada equipo
TEAM_KEYWORDS = {
    "Spain": ["Spain football", "España Mundial", "ver España"],
    "Brazil": ["Brazil football", "Brasil Mundial", "ver Brasil"],
    "Argentina": ["Argentina football", "Argentina Mundial", "Messi"],
    "France": ["France football", "Francia Mundial", "ver Francia"],
    "Germany": ["Germany football", "Alemania Mundial", "ver Alemania"],
    "England": ["England football", "Inglaterra Mundial", "ver Inglaterra"],
    "Portugal": ["Portugal football", "Portugal Mundial", "Ronaldo"],
    "Mexico": ["Mexico football", "Mexico Mundial", "ver Mexico"],
    "USA": ["USA football", "USMNT", "United States soccer"],
}

# Keywords económicos relacionados con el Mundial
ECONOMIC_KEYWORDS = [
    "watch World Cup",
    "stream World Cup",
    "World Cup streaming",
    "ver Mundial gratis",
    "World Cup tickets",
]


def get_trends_for_teams(home_team: str, away_team: str, timeframe: str = "now 1-d") -> list[dict]:
    """
    Obtiene tendencias de búsqueda para los dos equipos de un partido.
    timeframe: 'now 1-H' (última hora), 'now 1-d' (último día), 'now 7-d' (última semana)
    """
    try:
        pytrends = TrendReq(hl="en-US", tz=0)

        # Juntamos keywords de ambos equipos (máximo 5 en una llamada)
        home_keywords = TEAM_KEYWORDS.get(home_team, [f"{home_team} football"])[:2]
        away_keywords = TEAM_KEYWORDS.get(away_team, [f"{away_team} football"])[:2]
        keywords = (home_keywords + away_keywords + ["World Cup 2026"])[:5]

        pytrends.build_payload(keywords, timeframe=timeframe, geo="")
        data = pytrends.interest_over_time()

        if data.empty:
            logger.warning(f"Sin datos de tendencias para {home_team} vs {away_team}")
            return []

        results = []
        for timestamp, row in data.iterrows():
            for keyword in keywords:
                if keyword in row:
                    results.append({
                        "keyword": keyword,
                        "country": "WW",  # Worldwide
                        "interest_score": int(row[keyword]),
                        "timestamp_utc": timestamp.to_pydatetime().replace(tzinfo=timezone.utc),
                    })

        logger.info(f"Tendencias obtenidas para {home_team} vs {away_team}: {len(results)} registros")
        return results

    except Exception as e:
        logger.error(f"Error obteniendo tendencias para {home_team} vs {away_team}: {e}")
        return []


def get_economic_trends(timeframe: str = "now 7-d") -> list[dict]:
    """
    Obtiene tendencias de búsqueda para keywords económicos del Mundial.
    Útil para medir el interés en streaming, entradas, etc.
    """
    try:
        pytrends = TrendReq(hl="en-US", tz=0)
        keywords = ECONOMIC_KEYWORDS[:5]

        pytrends.build_payload(keywords, timeframe=timeframe, geo="")
        data = pytrends.interest_over_time()

        if data.empty:
            logger.warning("Sin datos de tendencias económicas")
            return []

        results = []
        for timestamp, row in data.iterrows():
            for keyword in keywords:
                if keyword in row:
                    results.append({
                        "keyword": keyword,
                        "country": "WW",
                        "interest_score": int(row[keyword]),
                        "timestamp_utc": timestamp.to_pydatetime().replace(tzinfo=timezone.utc),
                    })

        logger.info(f"Tendencias económicas obtenidas: {len(results)} registros")
        return results

    except Exception as e:
        logger.error(f"Error obteniendo tendencias económicas: {e}")
        return []


def get_trends_by_country(keyword: str, timeframe: str = "now 7-d") -> list[dict]:
    """
    Obtiene el interés de un keyword desglosado por país.
    Útil para ver qué países buscan más sobre el Mundial.
    """
    try:
        pytrends = TrendReq(hl="en-US", tz=0)
        pytrends.build_payload([keyword], timeframe=timeframe)
        data = pytrends.interest_by_region(resolution="COUNTRY")

        if data.empty:
            logger.warning(f"Sin datos por país para '{keyword}'")
            return []

        results = []
        timestamp = datetime.now(timezone.utc)
        for country, row in data.iterrows():
            score = int(row[keyword])
            if score > 0:
                results.append({
                    "keyword": keyword,
                    "country": country,
                    "interest_score": score,
                    "timestamp_utc": timestamp,
                })

        results.sort(key=lambda x: x["interest_score"], reverse=True)
        logger.info(f"Tendencias por país para '{keyword}': {len(results)} países")
        return results

    except Exception as e:
        logger.error(f"Error obteniendo tendencias por país: {e}")
        return []