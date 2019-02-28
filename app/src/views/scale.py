import sentry_sdk
from kubernetes import client
from kubernetes.client.rest import ApiException

__author__ = "Noah Hummel"


def get_scale_for_deployment(name: str, namespace: str) -> int:
    try:
        v1 = client.AppsV1Api()
        scale = v1.read_namespaced_deployment_scale(name, namespace)
        return scale.status.replicas
    except ApiException as e:
        sentry_sdk.capture_exception(e)
