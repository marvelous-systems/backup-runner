import sys

import logging

__author__ = "Noah Hummel"

_logger = None

def get():
    global _logger
    if not _logger:
        _logger = logging.getLogger("backup-runner")
        _logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        _logger.addHandler(handler)
    return _logger
