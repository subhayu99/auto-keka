import sys
import json
import logging
from datetime import datetime
from src.models import LogModel

class LoggingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        s = super().format(record)
        return LogModel(
            message=s,
            severity=record.levelname,
            timestamp=datetime.fromtimestamp(record.created).isoformat()[:-7],
        ).json()


def create_logger(level=logging.DEBUG):
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    formatter = LoggingFormatter(fmt="[%(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def get_logger(level=logging.INFO):
    create_logger(level)
    return logging.getLogger()
