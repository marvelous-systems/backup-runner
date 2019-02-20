import sys

import os

import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

__author__ = "Noah Hummel"


loggers = dict()

_sentry_dsn = os.environ.get("SENTRY_DSN")
if _sentry_dsn:
    sentry_logging = LoggingIntegration(
        level=logging.DEBUG,
        event_level=logging.WARNING
    )
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[sentry_logging]
    )


def get(name):
    if not loggers.get(name):
        logger = logging.getLogger(name)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        loggers[name] = logger
    return loggers.get(name)