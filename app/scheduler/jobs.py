from app.models.database import SessionLocal
from app.services.football_service import sync_matches, sync_live_match_events
from app.services.stock_service import sync_stock_snapshots
from app.services.news_service import sync_news
from app.services.correlation_service import run_all_correlations
from app.models.database import Match
from app.core.logger import logger


def job_sync_matches():
    """
    Sincroniza todos los partidos del Mundial.
    Se ejecuta cada 30 minutos.
    """
    logger.info("⚽ [JOB] Sincronizando partidos...")
    db = SessionLocal()
    try:
        count = sync_matches(db)
        logger.info(f"⚽ [JOB] Partidos sincronizados: {count}")
    except Exception as e:
        logger.error(f"⚽ [JOB] Error sincronizando partidos: {e}")
    finally:
        db.close()


def job_sync_live_data():
    """
    Sincroniza datos en tiempo real durante partidos en vivo:
    eventos, stocks y trends.
    Se ejecuta cada 5 minutos.
    """
    logger.info("🔴 [JOB] Comprobando partidos en vivo...")
    db = SessionLocal()
    try:
        # Verificar si hay partidos en vivo
        live_matches = db.query(Match).filter(Match.status == "LIVE").all()

        if not live_matches:
            logger.info("🔴 [JOB] Sin partidos en vivo, omitiendo sync de stocks")
            return

        logger.info(f"🔴 [JOB] {len(live_matches)} partido(s) en vivo — sincronizando datos económicos")

        # Sincronizar eventos del partido en vivo
        sync_live_match_events(db)

        # Capturar snapshot de stocks asociado al partido en vivo
        match_id = live_matches[0].id
        sync_stock_snapshots(db, match_id=match_id)

        logger.info("🔴 [JOB] Datos en vivo sincronizados correctamente")

    except Exception as e:
        logger.error(f"🔴 [JOB] Error en sync de datos en vivo: {e}")
    finally:
        db.close()


def job_sync_news():
    """
    Sincroniza noticias económicas del Mundial.
    Se ejecuta cada 60 minutos.
    """
    logger.info("📰 [JOB] Sincronizando noticias...")
    db = SessionLocal()
    try:
        count = sync_news(db)
        logger.info(f"📰 [JOB] Noticias nuevas: {count}")
    except Exception as e:
        logger.error(f"📰 [JOB] Error sincronizando noticias: {e}")
    finally:
        db.close()


def job_sync_stocks_idle():
    """
    Captura snapshots de stocks aunque no haya partidos en vivo.
    Se ejecuta cada 30 minutos para tener datos de referencia.
    """
    logger.info("📈 [JOB] Capturando snapshots de stocks (idle)...")
    db = SessionLocal()
    try:
        count = sync_stock_snapshots(db, match_id=None)
        logger.info(f"📈 [JOB] Snapshots guardados: {count}")
    except Exception as e:
        logger.error(f"📈 [JOB] Error capturando stocks: {e}")
    finally:
        db.close()


def job_calculate_correlations():
    """
    Calcula correlaciones entre eventos deportivos y métricas económicas.
    Se ejecuta cada 60 minutos.
    """
    logger.info("🔬 [JOB] Calculando correlaciones...")
    db = SessionLocal()
    try:
        count = run_all_correlations(db)
        logger.info(f"🔬 [JOB] Correlaciones calculadas: {count}")
    except Exception as e:
        logger.error(f"🔬 [JOB] Error calculando correlaciones: {e}")
    finally:
        db.close()