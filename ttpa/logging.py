"""Logging Module for TTPA"""


import logging

from ttpa.constants import LOG_FILE


def setup_logging(log_level=logging.INFO):
    """Set up logging for TTPA."""

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename=LOG_FILE,
    )
