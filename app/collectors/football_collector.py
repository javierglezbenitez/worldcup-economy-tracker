import requests
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logger import logger

# ID del Mundial 2026 en football-data.org
WORLD_CUP_ID = 2000
BASE_URL = "https://api.football-data.org/v4"

HEADERS = {
    "X-Auth-Token": settings.FOOTBALL_API_KEY
}


def get_matches() -> list[dict]:
    """Obtiene todos los partidos del Mundial 2026"""
    try:
        url = f"{BASE_URL}/competitions/{WORLD_CUP_ID}/matches"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        matches = data.get("matches", [])
        logger.info(f"Obtenidos {len(matches)} partidos del Mundial")
        return matches
    except requests.RequestException as e:
        logger.error(f"Error obteniendo partidos: {e}")
        return []


def get_live_matches() -> list[dict]:
    """Obtiene los partidos en curso ahora mismo"""
    try:
        url = f"{BASE_URL}/competitions/{WORLD_CUP_ID}/matches"
        response = requests.get(url, headers=HEADERS, params={"status": "LIVE"})
        response.raise_for_status()
        data = response.json()
        matches = data.get("matches", [])
        logger.info(f"Partidos en vivo: {len(matches)}")
        return matches
    except requests.RequestException as e:
        logger.error(f"Error obteniendo partidos en vivo: {e}")
        return []


def get_match_detail(match_id: int) -> dict | None:
    """Obtiene el detalle completo de un partido incluyendo eventos"""
    try:
        url = f"{BASE_URL}/matches/{match_id}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Detalle obtenido para partido {match_id}")
        return data
    except requests.RequestException as e:
        logger.error(f"Error obteniendo detalle del partido {match_id}: {e}")
        return None


def get_standings() -> list[dict]:
    """Obtiene las clasificaciones por grupo"""
    try:
        url = f"{BASE_URL}/competitions/{WORLD_CUP_ID}/standings"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        standings = data.get("standings", [])
        logger.info(f"Clasificaciones obtenidas: {len(standings)} grupos")
        return standings
    except requests.RequestException as e:
        logger.error(f"Error obteniendo clasificaciones: {e}")
        return []


def parse_match(raw: dict) -> dict:
    """
    Transforma un partido raw de la API al formato
    limpio que usará nuestra base de datos
    """
    home = raw.get("homeTeam", {})
    away = raw.get("awayTeam", {})
    score = raw.get("score", {})
    full_time = score.get("fullTime", {})

    return {
        "external_id": raw.get("id"),
        "home_team": home.get("name", "Unknown"),
        "away_team": away.get("name", "Unknown"),
        "home_score": full_time.get("home"),
        "away_score": full_time.get("away"),
        "stage": raw.get("stage"),
        "group": raw.get("group"),
        "venue": raw.get("venue"),
        "city": raw.get("area", {}).get("name"),
        "country": raw.get("area", {}).get("name"),
        "kickoff_utc": _parse_datetime(raw.get("utcDate")),
        "status": raw.get("status"),
    }


def parse_events(raw: dict, kickoff_utc: datetime) -> list[dict]:
    """
    Construye eventos a partir del resultado final del partido.
    El tier gratuito no da minutos exactos, así que estimamos
    los goles distribuyéndolos a lo largo del partido.
    """
    from datetime import timedelta
    import random

    events = []
    score = raw.get("score", {})
    full_time = score.get("fullTime", {})
    half_time = score.get("halfTime", {})

    home_team = raw.get("homeTeam", {}).get("name", "Home")
    away_team = raw.get("awayTeam", {}).get("name", "Away")

    home_goals = full_time.get("home") or 0
    away_goals = full_time.get("away") or 0
    home_half = half_time.get("home") or 0
    away_half = half_time.get("away") or 0

    # Goles del equipo local
    # Los de primera mitad entre minuto 1-45, los de segunda entre 46-90
    home_second_half = home_goals - home_half
    for i in range(home_half):
        minute = random.randint(5 * (i + 1), min(44, 5 * (i + 1) + 20))
        timestamp = kickoff_utc + timedelta(minutes=minute)
        events.append({
            "event_type": "GOAL",
            "minute": minute,
            "team": home_team,
            "player": None,
            "timestamp_utc": timestamp,
            "economic_window_start": timestamp - timedelta(minutes=30),
            "economic_window_end": timestamp + timedelta(minutes=60),
        })

    for i in range(home_second_half):
        minute = random.randint(46 + 5 * i, min(90, 46 + 5 * i + 20))
        timestamp = kickoff_utc + timedelta(minutes=minute)
        events.append({
            "event_type": "GOAL",
            "minute": minute,
            "team": home_team,
            "player": None,
            "timestamp_utc": timestamp,
            "economic_window_start": timestamp - timedelta(minutes=30),
            "economic_window_end": timestamp + timedelta(minutes=60),
        })

    # Goles del equipo visitante
    away_second_half = away_goals - away_half
    for i in range(away_half):
        minute = random.randint(5 * (i + 1), min(44, 5 * (i + 1) + 20))
        timestamp = kickoff_utc + timedelta(minutes=minute)
        events.append({
            "event_type": "GOAL",
            "minute": minute,
            "team": away_team,
            "player": None,
            "timestamp_utc": timestamp,
            "economic_window_start": timestamp - timedelta(minutes=30),
            "economic_window_end": timestamp + timedelta(minutes=60),
        })

    for i in range(away_second_half):
        minute = random.randint(46 + 5 * i, min(90, 46 + 5 * i + 20))
        timestamp = kickoff_utc + timedelta(minutes=minute)
        events.append({
            "event_type": "GOAL",
            "minute": minute,
            "team": away_team,
            "player": None,
            "timestamp_utc": timestamp,
            "economic_window_start": timestamp - timedelta(minutes=30),
            "economic_window_end": timestamp + timedelta(minutes=60),
        })

    # Evento de fin de partido — útil para análisis post-match
    end_timestamp = kickoff_utc + timedelta(minutes=95)
    events.append({
        "event_type": "MATCH_END",
        "minute": 95,
        "team": None,
        "player": None,
        "timestamp_utc": end_timestamp,
        "economic_window_start": end_timestamp - timedelta(minutes=30),
        "economic_window_end": end_timestamp + timedelta(minutes=60),
    })

    return events


def _parse_datetime(dt_str: str | None) -> datetime | None:
    """Convierte string ISO 8601 a datetime UTC"""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        logger.warning(f"No se pudo parsear fecha: {dt_str}")
        return None