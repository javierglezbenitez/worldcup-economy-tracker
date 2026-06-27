from sqlalchemy import (
    create_engine, Column, Integer, String,
    Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

from app.core.config import settings
from app.core.logger import logger

# Crear directorio data/ si no existe
os.makedirs("data", exist_ok=True)

# Configuración del motor SQLite
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Necesario para SQLite con FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─────────────────────────────────────────
# TABLA: matches
# ─────────────────────────────────────────
class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, index=True)  # ID de football-data.org
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    stage = Column(String)           # GROUP_STAGE, ROUND_OF_16...
    group = Column(String)           # Grupo A, B, C...
    venue = Column(String)
    city = Column(String)
    country = Column(String)
    kickoff_utc = Column(DateTime, nullable=False)
    status = Column(String)          # SCHEDULED, LIVE, FINISHED
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    events = relationship("MatchEvent", back_populates="match")
    stock_snapshots = relationship("StockSnapshot", back_populates="match")
    search_trends = relationship("SearchTrend", back_populates="match")
    news_sentiments = relationship("NewsSentiment", back_populates="match")


# ─────────────────────────────────────────
# TABLA: match_events
# ─────────────────────────────────────────
class MatchEvent(Base):
    __tablename__ = "match_events"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    event_type = Column(String)      # GOAL, RED_CARD, PENALTY, VAR, INJURY_TIME
    minute = Column(Integer)
    team = Column(String)
    player = Column(String, nullable=True)
    timestamp_utc = Column(DateTime, nullable=False)
    economic_window_start = Column(DateTime)   # timestamp - 30 min
    economic_window_end = Column(DateTime)     # timestamp + 60 min

    match = relationship("Match", back_populates="events")
    correlations = relationship("Correlation", back_populates="event")


# ─────────────────────────────────────────
# TABLA: stock_snapshots
# ─────────────────────────────────────────
class StockSnapshot(Base):
    __tablename__ = "stock_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    ticker = Column(String, nullable=False)
    company_name = Column(String)
    sponsor_country = Column(String)
    price = Column(Float)
    volume = Column(Float)
    change_pct = Column(Float)
    timestamp_utc = Column(DateTime, nullable=False)

    match = relationship("Match", back_populates="stock_snapshots")


# ─────────────────────────────────────────
# TABLA: search_trends
# ─────────────────────────────────────────
class SearchTrend(Base):
    __tablename__ = "search_trends"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    keyword = Column(String, nullable=False)
    country = Column(String)
    interest_score = Column(Integer)   # 0-100
    timestamp_utc = Column(DateTime, nullable=False)

    match = relationship("Match", back_populates="search_trends")


# ─────────────────────────────────────────
# TABLA: news_sentiment
# ─────────────────────────────────────────
class NewsSentiment(Base):
    __tablename__ = "news_sentiment"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    headline = Column(String, nullable=False)
    source = Column(String)
    category = Column(String)          # FINANCIAL, SPORTS, ADVERTISING, TOURISM
    sentiment_score = Column(Float)    # -1.0 a 1.0
    entities = Column(Text)            # JSON string con entidades detectadas
    timestamp_utc = Column(DateTime, nullable=False)

    match = relationship("Match", back_populates="news_sentiments")


# ─────────────────────────────────────────
# TABLA: correlations
# ─────────────────────────────────────────
class Correlation(Base):
    __tablename__ = "correlations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("match_events.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    correlation_type = Column(String)  # GOAL_TO_STOCK, ELIMINATION_TO_TRENDS...
    metric_before = Column(Float)
    metric_after = Column(Float)
    delta_pct = Column(Float)
    correlation_score = Column(Float)
    p_value = Column(Float)
    is_significant = Column(Boolean, default=False)  # p_value < 0.05
    calculated_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("MatchEvent", back_populates="correlations")


# ─────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────
def get_db():
    """Dependency para FastAPI — inyecta sesión de BD en cada request"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea todas las tablas si no existen"""
    Base.metadata.create_all(bind=engine)
    logger.info("Base de datos inicializada correctamente")