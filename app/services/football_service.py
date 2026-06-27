from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.database import Match, MatchEvent
from app.collectors.football_collector import (
    get_matches, get_live_matches, get_match_detail,
    get_standings, parse_match, parse_events
)
from app.core.logger import logger


def sync_matches(db: Session) -> int:
    """
    Sincroniza todos los partidos del Mundial con la base de datos.
    Inserta nuevos y actualiza los existentes.
    Retorna el número de partidos procesados.
    """
    raw_matches = get_matches()
    if not raw_matches:
        logger.warning("No se obtuvieron partidos de la API")
        return 0

    count = 0
    for raw in raw_matches:
        parsed = parse_match(raw)

        # Saltar si no hay ID
        if not parsed or not parsed.get("external_id"):
            continue

        # Saltar partidos sin equipos definidos todavía (fases eliminatorias pendientes)
        if not parsed.get("home_team") or not parsed.get("away_team"):
            logger.debug(f"Partido {parsed.get('external_id')} sin equipos definidos, omitiendo")
            continue

        # Buscar si ya existe en BD
        existing = db.query(Match).filter(
            Match.external_id == parsed["external_id"]
        ).first()

        if existing:
            # Actualizar campos que pueden cambiar
            existing.home_score = parsed["home_score"]
            existing.away_score = parsed["away_score"]
            existing.status = parsed["status"]
            existing.updated_at = datetime.now(timezone.utc)
        else:
            # Insertar nuevo partido
            match = Match(**parsed)
            db.add(match)

        count += 1

    db.commit()
    logger.info(f"Sincronizados {count} partidos en BD")
    return count


def sync_match_events(db: Session, match_id: int, external_id: int) -> int:
    """
    Sincroniza los eventos de un partido concreto.
    Retorna el número de eventos nuevos insertados.
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        logger.warning(f"Partido {match_id} no encontrado en BD")
        return 0

    raw_detail = get_match_detail(external_id)
    if not raw_detail:
        return 0

    parsed_events = parse_events(raw_detail, match.kickoff_utc)
    if not parsed_events:
        return 0

    count = 0
    for event_data in parsed_events:
        # Evitar duplicados por minuto y tipo de evento
        existing = db.query(MatchEvent).filter(
            MatchEvent.match_id == match_id,
            MatchEvent.event_type == event_data["event_type"],
            MatchEvent.minute == event_data["minute"],
            MatchEvent.team == event_data["team"],
        ).first()

        if not existing:
            event = MatchEvent(match_id=match_id, **event_data)
            db.add(event)
            count += 1

    db.commit()
    logger.info(f"Eventos sincronizados para partido {match_id}: {count} nuevos")
    return count


def sync_live_match_events(db: Session) -> int:
    """
    Sincroniza eventos de todos los partidos en vivo.
    Se llama cada 5 minutos durante partidos activos.
    """
    live_matches = get_live_matches()
    if not live_matches:
        logger.info("No hay partidos en vivo ahora mismo")
        return 0

    total_events = 0
    for raw in live_matches:
        external_id = raw.get("id")
        if not external_id:
            continue

        match = db.query(Match).filter(
            Match.external_id == external_id
        ).first()

        if match:
            events = sync_match_events(db, match.id, external_id)
            total_events += events

    return total_events


def get_matches_from_db(db: Session, status: str = None) -> list[Match]:
    """
    Obtiene partidos de la BD con filtro opcional por estado.
    status: SCHEDULED, LIVE, FINISHED
    """
    query = db.query(Match)
    if status:
        query = query.filter(Match.status == status)
    return query.order_by(Match.kickoff_utc).all()


def get_match_with_events(db: Session, match_id: int) -> Match | None:
    """Obtiene un partido con todos sus eventos"""
    return db.query(Match).filter(Match.id == match_id).first()


def get_standings_summary() -> dict:
    """
    Obtiene las clasificaciones actuales directamente de la API
    y las devuelve estructuradas por grupo
    """
    raw_standings = get_standings()
    if not raw_standings:
        return {}

    summary = {}
    for group in raw_standings:
        group_name = group.get("group", "Unknown")
        table = group.get("table", [])

        summary[group_name] = [
            {
                "position": row.get("position"),
                "team": row.get("team", {}).get("name"),
                "played": row.get("playedGames"),
                "won": row.get("won"),
                "draw": row.get("draw"),
                "lost": row.get("lost"),
                "goals_for": row.get("goalsFor"),
                "goals_against": row.get("goalsAgainst"),
                "goal_difference": row.get("goalDifference"),
                "points": row.get("points"),
            }
            for row in table
        ]

    logger.info(f"Clasificaciones estructuradas: {len(summary)} grupos")
    return summary