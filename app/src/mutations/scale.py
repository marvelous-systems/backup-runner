import random
import asyncio
from datetime import timedelta

import sentry_sdk
from kubernetes import client
from kubernetes.client.rest import ApiException

import logger
from k8s import check_resource, wait_for_reconciliation
from k8s.predicate import deployment_has_scale
from mutations.exceptions import ReconciliationError
from views.scale import get_scale_for_deployment

__author__ = "Noah Hummel"
log = logger.get(__name__)


def scale_deployment(name: str, namespace: str, replicas: int):
    try:
        appsV1 = client.AppsV1Api()
        current_scale = appsV1.read_namespaced_deployment_scale(name, namespace)
        current_scale.spec.replicas = replicas
        new_scale = appsV1.patch_namespaced_deployment_scale(name, namespace,
                                                             current_scale)
        log.debug(f"Updated deployment {namespace}/{name} spec to "
                  f"{new_scale.spec.replicas} replicas")
    except ApiException as e:
        sentry_sdk.capture_exception(e)


def scale_deployment_sync(name: str, namespace: str, replicas: int,
                          timeout: timedelta):
    """
    Same as scale_deployment, but waits for deployment scale to reach target.
    Returns and logs a warning after a certain timeout, if the deployment was
    not scaled to the target replica count.

    :param name: Name of the deployment
    :param namespace: Namespace containing Deployment
    :param replicas: Number of desired replicas
    :param timeout: Time after which to return without success
    """
    previous_replicas = get_scale_for_deployment(name, namespace)
    scale_deployment(name, namespace, replicas)

    try:
        v1 = client.AppsV1Api()
        predicate = deployment_has_scale(replicas)
        wait_for_reconciliation(predicate, timeout,
                                v1.read_namespaced_deployment, name, namespace)
    except ReconciliationError:
        log.warning(f"Deployment {namespace}/{name} could not be scaled to "
                    f"{replicas}, reverting to {previous_replicas}.")
        scale_deployment(name, namespace, previous_replicas)
