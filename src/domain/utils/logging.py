import logging
import sys
from datetime import UTC, datetime
from typing import Any, TextIO, cast

import orjson


class LoggingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:

        log_record: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        extra_data: dict | None = getattr(record, "extra", None)
        if isinstance(extra_data, dict):
            log_record.update(cast(dict[str, Any], extra_data))

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return orjson.dumps(log_record).decode("utf-8")


def setup_logging():
    """
    Initializes the global logging system.
    This connects the LoggingFormatter to the root of the application.
    """
    # 1. Create the 'Physical' output (Standard Out for Docker/Cloud)
    handler: logging.StreamHandler[TextIO | Any] = logging.StreamHandler(sys.stdout)

    # 2. Attach your custom 'Blueprint' to the output
    handler.setFormatter(LoggingFormatter())

    # 3. Configure the Root Logger (The boss of all loggers)
    root_logger: logging.Logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    # 4. Clean up noise from libraries (Optional but recommended)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
