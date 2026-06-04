"""Structured logging configuration for the Tragedy simulation system."""

from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO", fmt: str = "console") -> None:
    """Configure the root logger for Tragedy.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR).
        fmt: Output format — "console" for human-readable or "json" for structured.
    """
    root = logging.getLogger("tragedy")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    root.handlers.clear()

    if fmt == "json":
        try:
            import structlog

            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.JSONRenderer(),
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                cache_logger_on_first_use=True,
            )
        except ImportError:
            pass
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        root.addHandler(handler)
