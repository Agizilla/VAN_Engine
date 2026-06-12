import logging
import sys
from pathlib import Path
from typing import Optional

from colorlog import ColoredFormatter


def setup_logging(
    name: str = "clawdia",
    level: str = "INFO",
    log_file: Optional[str] = None,
    debug: bool = False,
):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if debug else getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if debug else getattr(logging, level.upper(), logging.INFO))
    console_fmt = ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)-8s] %(name)s: %(message)s%(reset)s",
        datefmt="%H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
    console.setFormatter(console_fmt)
    logger.addHandler(console)

    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh_fmt = logging.Formatter("%(asctime)s [%(levelname)-8s] %(name)s: %(message)s")
        fh.setFormatter(fh_fmt)
        logger.addHandler(fh)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name or "clawdia")
