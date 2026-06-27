from loguru import logger
import sys

logger.remove()  # Elimina el handler por defecto

# Logs en consola con formato limpio
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan> - {message}",
    level="INFO"
)

# Logs en fichero para debug
logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG"
)