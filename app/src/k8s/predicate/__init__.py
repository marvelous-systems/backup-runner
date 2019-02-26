from kubernetes.client import V1Deployment, V1PersistentVolumeClaim
from typing import Callable

import logger

__author__ = "Noah Hummel"
log = logger.get(__name__)



def deployment_has_scale(replicas: int) -> Callable:
    if replicas == 0:
        replicas = None

    def _deployment_has_scale(deployment: V1Deployment) -> bool:
        return deployment.status.replicas == replicas

    return _deployment_has_scale


def pvc_is_unbound(pvc: V1PersistentVolumeClaim) -> bool:
    return pvc.status.phase == "Unbound"
