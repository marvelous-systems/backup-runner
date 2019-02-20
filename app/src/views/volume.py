import sentry_sdk
from typing import List

from kubernetes import client
from kubernetes.client import V1Volume, V1Deployment
from kubernetes.client.rest import ApiException

__author__ = "Noah Hummel"


def list_volumes_for_deployment(name: str, namespace: str) \
        -> List[V1Volume]:
    try:
        api = client.AppsV1Api()
        deployment: V1Deployment = api.read_namespaced_deployment(name,
                                                                  namespace)
        volumes = deployment.spec.template.spec.volumes
        return volumes if volumes else []
    except ApiException as e:
        sentry_sdk.capture_exception(e)
