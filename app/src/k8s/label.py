from typing import Dict

import logger

__author__ = "Noah Hummel"
log = logger.get(__name__)


def label_selector(*labels: Dict[str, str]) -> str:
    selectors = []
    for label in labels:
        key = next(label.keys().__iter__())
        selectors.append(f"{key}={label[key]}")
    return ",".join(selectors)
