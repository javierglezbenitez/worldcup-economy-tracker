from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.config import settings
from app.core.logger import logger
from app.scheduler.jobs import (
    job_sync_matches,
    job_sync_live_data,
    job_sync_news,
    job_sync_stocks_idle,
    job_calculate_correlations,
    job_detect_live_matches
)

scheduler = BackgroundScheduler()


def start_scheduler():
    """
    Registra y arranca todos los jobs del scheduler.
    Se llama al iniciar la aplicación FastAPI.
    """

    # Sincronizar partidos cada 30 minutos
    scheduler.add_job(
        job_sync_matches,
        trigger=IntervalTrigger(minutes=30),
        id="sync_matches",
        name="Sincronizar partidos",
        replace_existing=True,
    )

    # Detectar partidos en vivo cada 2 minutos (evita perder partidos cortos entre syncs largos)
    scheduler.add_job(
        job_detect_live_matches,
        trigger=IntervalTrigger(minutes=2),
        id="detect_live_matches",
        name="Detectar partidos en vivo",
        replace_existing=True,
    )

    # Datos en vivo cada 5 minutos
    scheduler.add_job(
        job_sync_live_data,
        trigger=IntervalTrigger(minutes=settings.POLLING_INTERVAL_LIVE),
        id="sync_live_data",
        name="Sincronizar datos en vivo",
        replace_existing=True,
    )

    # Noticias cada 60 minutos
    scheduler.add_job(
        job_sync_news,
        trigger=IntervalTrigger(minutes=60),
        id="sync_news",
        name="Sincronizar noticias",
        replace_existing=True,
    )

    # Stocks en reposo cada 30 minutos
    scheduler.add_job(
        job_sync_stocks_idle,
        trigger=IntervalTrigger(minutes=settings.POLLING_INTERVAL_IDLE),
        id="sync_stocks_idle",
        name="Snapshots stocks idle",
        replace_existing=True,
    )

    # Correlaciones cada 60 minutos
    scheduler.add_job(
        job_calculate_correlations,
        trigger=IntervalTrigger(minutes=60),
        id="calculate_correlations",
        name="Calcular correlaciones",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("✅ Scheduler arrancado con 6 jobs activos")

def stop_scheduler():
    """Para el scheduler limpiamente al cerrar la app"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 Scheduler detenido")