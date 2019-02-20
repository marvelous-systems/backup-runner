import sentry_sdk

__author__ = "Noah Hummel"

from kubernetes import client
from kubernetes.client.rest import ApiException
import logger

log = logger.get(__name__)


def scale_deployment(name: str, namespace: str, replicas: int):
    try:
        log.debug(f"Scaling deployment {name} in {namespace} to {replicas}")
        appsV1 = client.AppsV1Api()
        current_scale = appsV1.read_namespaced_deployment_scale(name, namespace)
        current_scale.spec.replicas = replicas
        new_scale = appsV1.patch_namespaced_deployment_scale(name, namespace,
                                                             current_scale)
        log.debug(f"Scaled to {new_scale.spec.replicas} replicas")
    except ApiException as e:
        sentry_sdk.capture_exception(e)
