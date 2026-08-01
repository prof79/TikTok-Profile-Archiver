"""Logging Module for TTPA"""


import logging

from typing import Callable

from mmeutils.textio import strip_rich_tags
from rich import print

from ttpa.constants import LOG_FILE


def setup_logging(log_level=logging.INFO):
    """Set up logging for TTPA."""

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename=LOG_FILE,
    )


def log_basic(message: str, log_func: Callable=logging.info) -> None:
    print(message)
    log_func(strip_rich_tags(message))


def log_info(message) -> None:
    log_basic(message)


def log_warning(message) -> None:
    log_basic(message, logging.warning)


def log_error(message) -> None:
    log_basic(message, logging.error)


def log_debug(message) -> None:
    if logging.getLevelName(logging.root.level) == 'DEBUG':
        log_basic(message, logging.debug)
