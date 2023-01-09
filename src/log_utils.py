import json
import logging
import sys


class CloudLoggingFormatter(logging.Formatter):
    """Produces messages compatible with google cloud logging"""

    def format(self, record: logging.LogRecord) -> str:
        s = super().format(record)
        return json.dumps(
            {
                "message": s,
                "severity": record.levelname,
                "timestamp": {"seconds": int(record.created), "nanos": 0},
            }
        )


def create_logger(level=logging.DEBUG):
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    formatter = CloudLoggingFormatter(fmt="[%(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def cloud_logger(level=logging.DEBUG):
    create_logger(level)
    return logging.getLogger()
