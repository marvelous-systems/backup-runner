from kubernetes import client
from kubernetes.client import V1Deployment

from typing import Dict

import logger

__author__ = "Noah Hummel"
log = logger.get(__name__)


def create_deployment(body: Dict, namespace: str) -> V1Deployment:
    log.debug(f"Creating Deployment {namespace}/{body['metadata']['name']}: "
              f"{body}")
    api = client.AppsV1Api()
    return api.create_namespaced_deployment(namespace, body)
