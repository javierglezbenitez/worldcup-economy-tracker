from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
from fastapi.responses import JSONResponse
from app.core.logger import logger
from app.core.config import settings
from app.models.database import get_db, init_db, Match, MatchEvent, StockSnapshot, NewsSentiment
from app.models.schemas import (
    MatchResponse, MatchWithEvents, MatchEventResponse,
    StockSnapshotResponse, SearchTrendResponse,
    NewsSentimentResponse, CorrelationResponse,
    HealthResponse, SentimentSummary, StockSummary
)
from app.services.football_service import (
    sync_matches, get_matches_from_db,
    get_match_with_events, get_standings_summary
)
from app.services.stock_service import (
    sync_stock_snapshots, get_latest_snapshots,
    get_stock_history, get_snapshots_during_match
)
from app.services.news_service import (
    sync_news, get_sentiment_summary,
    get_latest_news, get_most_mentioned_entities
)
from app.services.correlation_service import (
    run_all_correlations, get_significant_correlations,
    get_correlations_summary
)
from app.scheduler.scheduler import start_scheduler, stop_scheduler
from app.services.llm_service import chat as llm_chat
from pydantic import BaseModel

# ─────────────────────────────────────────
# LIFESPAN — arranque y cierre de la app
# ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Arranque
    logger.info("🚀 Arrancando World Cup Economy Tracker...")
    init_db()
    sync_matches(next(get_db()))
    start_scheduler()
    logger.info("✅ Aplicación lista")
    yield
    # Cierre
    stop_scheduler()
    logger.info("🛑 Aplicación cerrada")


# ─────────────────────────────────────────
# APP FASTAPI
# ─────────────────────────────────────────
app = FastAPI(
    title="World Cup Economy Tracker",
    description="Uncovering hidden economic correlations during the 2026 FIFA World Cup",
    version="1.0.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────
@app.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    from app.models.database import MatchEvent, StockSnapshot, NewsSentiment
    return HealthResponse(
        status="ok",
        last_update=datetime.now(timezone.utc),
        matches_count=db.query(Match).count(),
        events_count=db.query(MatchEvent).count(),
        snapshots_count=db.query(StockSnapshot).count(),
        news_count=db.query(NewsSentiment).count(),
    )


# ─────────────────────────────────────────
# MATCHES
# ─────────────────────────────────────────
@app.get("/matches", response_model=list[MatchResponse])
def get_matches(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Todos los partidos del Mundial con filtro opcional por estado"""
    return get_matches_from_db(db, status=status)


@app.get("/matches/live", response_model=list[MatchResponse])
def get_live_matches(db: Session = Depends(get_db)):
    """Partidos en curso ahora mismo (incluye descanso)"""
    from app.models.database import Match
    return db.query(Match).filter(Match.status.in_(["LIVE", "IN_PLAY", "PAUSED"])).all()


@app.get("/matches/{match_id}", response_model=MatchWithEvents)
def get_match(match_id: int, db: Session = Depends(get_db)):
    """Detalle de un partido con sus eventos"""
    match = get_match_with_events(db, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return match


# ─────────────────────────────────────────
# STANDINGS
# ─────────────────────────────────────────
@app.get("/standings")
def get_standings():
    """Clasificaciones actuales por grupo"""
    return get_standings_summary()


@app.get("/standings/{group}")
def get_group_standings(group: str):
    """Clasificación de un grupo concreto (ej: Group A)"""
    standings = get_standings_summary()

    # Intentar varias variantes del nombre
    possible_keys = [
        group,  # "Group A" tal cual
        group.upper(),  # "GROUP A"
        group.replace("_", " "),  # "GROUP_A" → "GROUP A"
        group.replace("_", " ").title()  # "GROUP_A" → "Group A"
    ]

    for key in possible_keys:
        if key in standings:
            return standings[key]

    raise HTTPException(status_code=404, detail=f"Grupo {group} no encontrado")


# ─────────────────────────────────────────
# STOCKS
# ─────────────────────────────────────────
@app.get("/stocks/snapshots")
def get_stock_snapshots(db: Session = Depends(get_db)):
    """Últimos precios de todos los sponsors"""
    return get_latest_snapshots(db)


@app.get("/stocks/{ticker}/history")
def get_ticker_history(ticker: str, hours: int = 24, db: Session = Depends(get_db)):
    """Histórico de un ticker en las últimas N horas"""
    history = get_stock_history(db, ticker.upper(), hours=hours)
    if not history:
        raise HTTPException(status_code=404, detail=f"Sin datos para {ticker}")
    return history


@app.get("/stocks/during/{match_id}")
def get_stocks_during_match(match_id: int, db: Session = Depends(get_db)):
    """Cotizaciones capturadas durante un partido concreto"""
    return get_snapshots_during_match(db, match_id)


# ─────────────────────────────────────────
# SENTIMENT & NEWS
# ─────────────────────────────────────────
@app.get("/sentiment")
def get_sentiment(db: Session = Depends(get_db)):
    """Últimas noticias con análisis de sentimiento"""
    return get_latest_news(db, limit=20)


@app.get("/sentiment/summary")
def get_sentiment_summary_endpoint(db: Session = Depends(get_db)):
    """Resumen de sentimiento por categoría económica"""
    return get_sentiment_summary(db)


@app.get("/sentiment/entities")
def get_entities(db: Session = Depends(get_db)):
    """Entidades económicas más mencionadas en noticias"""
    return get_most_mentioned_entities(db)


# ─────────────────────────────────────────
# CORRELATIONS
# ─────────────────────────────────────────
@app.get("/correlations")
def get_correlations(db: Session = Depends(get_db)):
    """Resumen de todas las correlaciones calculadas"""
    return get_correlations_summary(db)


@app.get("/correlations/significant")
def get_significant(db: Session = Depends(get_db)):
    """Solo correlaciones estadísticamente significativas (p < 0.05)"""
    return get_significant_correlations(db)


@app.get("/correlations/{event_type}")
def get_correlations_by_type(event_type: str, db: Session = Depends(get_db)):
    """Correlaciones filtradas por tipo de evento"""
    from app.models.database import Correlation
    correlations = db.query(Correlation).filter(
        Correlation.correlation_type == event_type.upper()
    ).all()
    if not correlations:
        raise HTTPException(status_code=404, detail=f"Sin correlaciones para {event_type}")
    return correlations


# ─────────────────────────────────────────
# TRIGGER MANUAL (útil para testing)
# ─────────────────────────────────────────
@app.post("/admin/sync")
def manual_sync(db: Session = Depends(get_db)):
    """Fuerza una sincronización manual de todos los datos"""
    matches = sync_matches(db)
    stocks = sync_stock_snapshots(db)
    news = sync_news(db)
    correlations = run_all_correlations(db)
    return {
        "matches_synced": matches,
        "stocks_synced": stocks,
        "news_synced": news,
        "correlations_calculated": correlations,
    }



class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

@app.post("/chat")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Endpoint del agente conversacional con contexto del Mundial"""
    response = llm_chat(
        db=db,
        messages=request.history,
        user_message=request.message
    )
    return {"response": response}


@app.head("/health")
def health_head():
    """HEAD request para UptimeRobot"""
    return JSONResponse(content={}, status_code=200)


@app.get("/bracket")
def get_bracket(db: Session = Depends(get_db)):
    """Devuelve todos los partidos de eliminatorias agrupados por fase"""
    knockout_stages = ["LAST_32", "LAST_16", "QUARTER_FINALS", "SEMI_FINALS", "THIRD_PLACE", "FINAL"]
    matches = db.query(Match).filter(Match.stage.in_(knockout_stages)).order_by(Match.kickoff_utc).all()

    bracket = {stage: [] for stage in knockout_stages}
    for m in matches:
        bracket[m.stage].append({
            "id": m.id,
            "home_team": m.home_team,
            "away_team": m.away_team,
            "home_score": m.home_score,
            "away_score": m.away_score,
            "status": m.status,
            "kickoff_utc": m.kickoff_utc,
        })
    return bracket