import asyncio

from datetime import timedelta

import sentry_sdk
from kubernetes import client
from kubernetes.client.rest import ApiException

import logger
from k8s import wait_for_reconciliation
from k8s.predicate import deployment_has_scale
from mutations.exceptions import ReconciliationError
from views.scale import get_scale_for_deployment

__author__ = "Noah Hummel"
log = logger.get(__name__)


def update_deployment_scale(name: str, namespace: str, replicas: int):
    """Updates a Deployment to scale to a certain amount of replicas.

    Does not wait for the cluster state to update to the desired state.

    Args:
        name: Name of the Deployment.
        namespace: Namespace of the Deployment.
        replicas: Desired number of replicas.
    """
    try:
        api = client.AppsV1Api()
        current_scale = api.read_namespaced_deployment_scale(name, namespace)
        current_scale.spec.replicas = replicas
        new_scale = api.patch_namespaced_deployment_scale(name, namespace,
                                                          current_scale)
        log.debug(f"Updated deployment {namespace}/{name} spec to "
                  f"{new_scale.spec.replicas} replicas")
    except ApiException as e:
        sentry_sdk.capture_exception(e)


async def scale_deployment(name: str, namespace: str, replicas: int,
                           timeout: timedelta):
    """Updates a Deployment's scale and waits for cluster state to reconcile.

    Args:
        name: Name of the Deployment.
        namespace: Namespace of the Deployment.
        replicas: Desired number of replicas.
        timeout: Time to wait for reconciliation until failing.

    Raises:
        ReconciliationError:
            The cluster state did not reconcile within timeout.
    """
    previous_replicas = get_scale_for_deployment(name, namespace)
    update_deployment_scale(name, namespace, replicas)

    try:
        api = client.AppsV1Api()
        predicate = deployment_has_scale(replicas)
        await wait_for_reconciliation(
            predicate,
            timeout,
            api.read_namespaced_deployment,
            name,
            namespace
        )
    except ReconciliationError:
        log.warning(f"Deployment {namespace}/{name} could not be scaled to "
                    f"{replicas}, reverting to {previous_replicas}.")
        update_deployment_scale(name, namespace, previous_replicas)


def scale_deployment_blocking(name: str, namespace: str, replicas: int,
                              timeout: timedelta):
    """Updates a Deployment's scale and waits for cluster state to reconcile.

    Args:
        name: Name of the Deployment.
        namespace: Namespace of the Deployment.
        replicas: Desired number of replicas.
        timeout: Time to wait for reconciliation until failing.

    Raises:
        ReconciliationError:
            The cluster state did not reconcile within timeout.
    """
    asyncio.run(scale_deployment(name, namespace, replicas, timeout))
