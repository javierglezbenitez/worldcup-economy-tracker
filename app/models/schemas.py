from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ─────────────────────────────────────────
# SCHEMAS DE MATCH
# ─────────────────────────────────────────
class MatchBase(BaseModel):
    external_id: int
    home_team: str
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    stage: Optional[str] = None
    group: Optional[str] = None
    venue: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    kickoff_utc: datetime
    status: str


class MatchResponse(MatchBase):
    id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# SCHEMAS DE MATCH EVENT
# ─────────────────────────────────────────
class MatchEventBase(BaseModel):
    event_type: str
    minute: Optional[int] = None
    team: Optional[str] = None
    player: Optional[str] = None
    timestamp_utc: datetime
    economic_window_start: Optional[datetime] = None
    economic_window_end: Optional[datetime] = None


class MatchEventResponse(MatchEventBase):
    id: int
    match_id: int

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# SCHEMAS DE STOCK
# ─────────────────────────────────────────
class StockSnapshotBase(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    sponsor_country: Optional[str] = None
    price: float
    volume: Optional[float] = None
    change_pct: float
    timestamp_utc: datetime


class StockSnapshotResponse(StockSnapshotBase):
    id: int
    match_id: Optional[int] = None

    class Config:
        from_attributes = True


class StockSummary(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    current_price: float
    change_pct: float
    trend: str = Field(description="UP / DOWN / NEUTRAL")
    snapshots_count: int


# ─────────────────────────────────────────
# SCHEMAS DE TRENDS
# ─────────────────────────────────────────
class SearchTrendBase(BaseModel):
    keyword: str
    country: Optional[str] = None
    interest_score: int = Field(ge=0, le=100)
    timestamp_utc: datetime


class SearchTrendResponse(SearchTrendBase):
    id: int
    match_id: Optional[int] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# SCHEMAS DE NEWS SENTIMENT
# ─────────────────────────────────────────
class NewsSentimentBase(BaseModel):
    headline: str
    source: Optional[str] = None
    category: str
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    entities: Optional[str] = None  # JSON string
    timestamp_utc: datetime


class NewsSentimentResponse(NewsSentimentBase):
    id: int
    match_id: Optional[int] = None

    class Config:
        from_attributes = True


class SentimentSummary(BaseModel):
    category: str
    avg_sentiment: float
    total_articles: int
    positive: int
    negative: int
    neutral: int
    sentiment_label: str = Field(description="POSITIVE / NEGATIVE / NEUTRAL")


# ─────────────────────────────────────────
# SCHEMAS DE CORRELACIONES
# ─────────────────────────────────────────
class CorrelationBase(BaseModel):
    correlation_type: str
    metric_before: Optional[float] = None
    metric_after: Optional[float] = None
    delta_pct: Optional[float] = None
    correlation_score: Optional[float] = None
    p_value: Optional[float] = None
    is_significant: bool = False


class CorrelationResponse(CorrelationBase):
    id: int
    event_id: int
    match_id: int
    calculated_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# SCHEMAS GENERALES
# ─────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    last_update: Optional[datetime] = None
    matches_count: int
    events_count: int
    snapshots_count: int
    news_count: int


class MatchWithEvents(MatchResponse):
    events: List[MatchEventResponse] = []

    class Config:
        from_attributes = True