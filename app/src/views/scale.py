from kubernetes import client

__author__ = "Noah Hummel"


def get_scale_for_deployment(name: str, namespace: str) -> int:
    v1 = client.AppsV1Api()
    scale = v1.read_namespaced_deployment_scale(name, namespace)
    return scale.status.replicas
