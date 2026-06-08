import json
import logging
import logging.config
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

import colorlog


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        for key in ("job_id", "lead_id"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        extra = getattr(record, "extra", None)
        if extra is not None:
            payload["extra"] = extra
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    console = colorlog.StreamHandler()
    console.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(cyan)s%(name)s%(reset)s %(message)s",
            log_colors={
                "DEBUG": "white",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    )

    app_file = RotatingFileHandler("logs/app.log", maxBytes=10 * 1024 * 1024, backupCount=5)
    app_file.setFormatter(JsonFormatter())

    root.addHandler(console)
    root.addHandler(app_file)

    for name, path in {"scraper": "logs/scraper.log", "email": "logs/email.log"}.items():
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(path, maxBytes=10 * 1024 * 1024, backupCount=5)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = True
