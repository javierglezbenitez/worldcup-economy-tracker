from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Keys
    FOOTBALL_API_KEY: str
    NEWS_API_KEY: str

    # Añadir después de NEWS_API_KEY
    GROQ_API_KEY: str

    # Base de datos
    DATABASE_URL: str = "sqlite:///./data/mundial2026.db"

    # Scheduler
    POLLING_INTERVAL_LIVE: int = 5    # minutos durante partido en vivo
    POLLING_INTERVAL_IDLE: int = 30   # minutos en reposo

    # Sponsors a trackear
    STOCK_TICKERS: str = "ADDYY,NKE,KO,BUD,V,BABA,FOX"

    @property
    def tickers_list(self) -> List[str]:
        return self.STOCK_TICKERS.split(",")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instancia global — el resto del proyecto importa esto
settings = Settings()