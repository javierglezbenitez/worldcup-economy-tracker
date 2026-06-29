import requests
from datetime import datetime, timezone, timedelta
from textblob import TextBlob
import json
from app.core.config import settings
from app.core.logger import logger

BASE_URL = "https://newsapi.org/v2/everything"

# Queries de búsqueda por categoría económica
SEARCH_QUERIES = {
    "FINANCIAL": "World Cup sponsors Nike Adidas",
    "ADVERTISING": "World Cup 2026 advertising broadcast",
    "TOURISM": "World Cup 2026 economy revenue",
    "STREAMING": "World Cup 2026 streaming audience",
}

# Entidades económicas clave que queremos detectar en las noticias
ECONOMIC_ENTITIES = [
    # Sponsors
    "Nike", "Adidas", "Coca-Cola", "Budweiser", "Visa", "Alibaba", "Fox",
    # Selecciones grandes (impacto económico)
    "Spain", "Brazil", "Argentina", "France", "Germany", "England", "Portugal",
    # Conceptos económicos
    "advertising", "sponsorship", "broadcast", "streaming", "revenue",
    "tourism", "ticket", "investment", "stock", "shares",
]


def get_news(category: str, days_back: int = 1) -> list[dict]:
    """
    Obtiene noticias económicas relacionadas con el Mundial.
    days_back: cuántos días hacia atrás buscar
    """
    try:
        query = SEARCH_QUERIES.get(category, "World Cup 2026 economy")
        from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")

        params = {
            "q": query,
            "from": from_date,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 20,
            "apiKey": settings.NEWS_API_KEY,
        }

        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])
        logger.info(f"Noticias [{category}]: {len(articles)} artículos obtenidos")
        return articles

    except requests.RequestException as e:
        logger.error(f"Error obteniendo noticias [{category}]: {e}")
        return []


def analyze_sentiment(text: str) -> float:
    """
    Calcula el sentimiento de un texto.
    Retorna un score entre -1.0 (muy negativo) y 1.0 (muy positivo)
    """
    if not text:
        return 0.0
    blob = TextBlob(text)
    return round(blob.sentiment.polarity, 4)


def extract_entities(text: str) -> list[str]:
    """
    Detecta qué entidades económicas relevantes
    aparecen en el texto de la noticia
    """
    if not text:
        return []
    text_lower = text.lower()
    found = [entity for entity in ECONOMIC_ENTITIES if entity.lower() in text_lower]
    return list(set(found))


def parse_article(article: dict, category: str) -> dict | None:
    """
    Transforma un artículo raw en un registro limpio
    con sentimiento y entidades detectadas
    """
    headline = article.get("title", "")
    description = article.get("description", "")

    if not headline or headline == "[Removed]":
        return None

    # Analizamos sentimiento sobre título + descripción
    full_text = f"{headline}. {description}"
    sentiment = analyze_sentiment(full_text)
    entities = extract_entities(full_text)

    published_at = article.get("publishedAt")
    timestamp = None
    if published_at:
        try:
            timestamp = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except ValueError:
            timestamp = datetime.now(timezone.utc)

    return {
        "headline": headline[:500],  # Limitamos longitud
        "url": article.get("url"),        # ← añadir esta línea
        "source": article.get("source", {}).get("name", "Unknown"),
        "category": category,
        "sentiment_score": sentiment,
        "entities": json.dumps(entities),
        "timestamp_utc": timestamp or datetime.now(timezone.utc),
    }


def get_all_news() -> list[dict]:
    """
    Obtiene y procesa noticias de todas las categorías económicas.
    Retorna lista de artículos parseados y listos para guardar en BD.
    """
    all_articles = []

    for category in SEARCH_QUERIES.keys():
        raw_articles = get_news(category, days_back=7)
        for article in raw_articles:
            parsed = parse_article(article, category)
            if parsed:
                all_articles.append(parsed)

    # Eliminamos duplicados por headline
    seen = set()
    unique_articles = []
    for article in all_articles:
        if article["headline"] not in seen:
            seen.add(article["headline"])
            unique_articles.append(article)

    logger.info(f"Total noticias procesadas: {len(unique_articles)} únicas")
    return unique_articles