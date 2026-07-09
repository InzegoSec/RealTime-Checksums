import logging
import os
from logging.handlers import RotatingFileHandler
from config import LOG_DIR_PATH

def initializeLoggers() -> None:
    os.makedirs(LOG_DIR_PATH, exist_ok=True)
    logger1 = logging.getLogger("infoLogger")
    logger1.setLevel(logging.INFO)
    logger2 = logging.getLogger("alertLogger")
    logger2.setLevel(logging.WARNING)
    format = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    if not logger1.handlers and not logger2.handlers:
        handler1 = RotatingFileHandler(LOG_DIR_PATH + "info.log", maxBytes=5*1024*1024, backupCount=3)
        handler1.setFormatter(format)
        logger1.addHandler(handler1)

        handler2 = RotatingFileHandler(LOG_DIR_PATH + "alerts.log", maxBytes=5*1024*1024, backupCount=3)
        handler2.setFormatter(format)
        logger2.addHandler(handler2)

def logInfo(message: str) -> None:
    logger = logging.getLogger("infoLogger")
    logger.info(message)

def logAlert(message: str) -> None:
    logger = logging.getLogger("alertLogger")
    logger.warning(message)

def logError(message: str) -> None:
    logger = logging.getLogger("infoLogger")
    logger.error(message)
