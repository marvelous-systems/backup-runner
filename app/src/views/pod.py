from kubernetes import client
from kubernetes.client import V1Pod, V1Deployment
from kubernetes.client.rest import ApiException
from typing import List

import logger
from k8s.label import label_selector

__author__ = "Noah Hummel"
log = logger.get(__name__)


def list_pods_for_deployment(name: str, namespace: str) -> List[V1Pod]:
    try:
        apps = client.AppsV1Api()
        core = client.CoreV1Api()
        deployment: V1Deployment = apps.read_namespaced_deployment(name,
                                                                   namespace)
        labels = deployment.spec.selector.match_labels
        selector = label_selector(labels)
        podlist = core.list_namespaced_pod(namespace, label_selector=selector)
        return podlist.items
    except ApiException as e:
        log.warning(f"Could not fetch Deployment {namespace}/{name}: "
                    f"{e.reason}")
        return []