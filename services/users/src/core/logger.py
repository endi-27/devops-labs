import logging
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from src.core.config import settings


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame: Any = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    logger.remove()

    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level> <magenta>{extra}</magenta>"
    )

    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.log.level,
        colorize=True,
        enqueue=True,
    )

    logging.getLogger("watchfiles.main").setLevel(logging.WARNING)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for uvicorn_logger in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(uvicorn_logger).handlers = [InterceptHandler()]

    if settings.is_testing:
        return

    log_dir = Path(settings.log.dir)
    app_log_path = log_dir / settings.log.app_file
    app_log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(app_log_path),
        rotation=settings.log.rotation,
        retention=settings.log.retention,
        compression="zip",
        level=settings.log.level,
        enqueue=True,
        encoding="utf-8",
    )


__all__ = ["InterceptHandler", "logger", "setup_logging"]
