from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "context"):
            payload["context"] = getattr(record, "context")
        return json.dumps(payload)


def build_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        logger.setLevel(level.upper())
        return logger

    logger.setLevel(level.upper())
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger
