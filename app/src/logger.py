import os
import sys

import logging
from raven import Client
from raven.handlers.logging import SentryHandler

__author__ = "Noah Hummel"

_loggers = dict()

def get(name):
    global _loggers
    if not _loggers.get(name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Sentry handler
        sentry_dsn = os.environ.get("SENTRY_DSN")
        logger.debug("Setting up sentry logging")
        if sentry_dsn:
            client = Client(sentry_dsn)
            sentry = SentryHandler(client)
            sentry.setLevel(logging.WARNING)
            logger.addHandler(sentry)

        _loggers[name] = logger

    return _loggers[name]
