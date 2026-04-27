from __future__ import annotations

import logging
import os
import sys


class _ServiceFilter(logging.Filter):
    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name

    def filter(self, record: logging.LogRecord) -> bool:
        record.service_name = self._service_name
        return True


def configure_logging(service_name: str) -> logging.Logger:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s service=%(service_name)s logger=%(name)s %(message)s",
        force=True,
    )
    # Attach the filter to every existing handler so propagated records from
    # child loggers (httpx, openai, uvicorn, ...) also pick up service_name.
    # Filters set on the root logger don't run for propagated records — only
    # ancestor handlers do — so the filter must live on the handler.
    service_filter = _ServiceFilter(service_name)
    for handler in logging.getLogger().handlers:
        handler.addFilter(service_filter)
    return logging.getLogger(service_name)

