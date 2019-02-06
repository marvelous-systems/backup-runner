import sentry_sdk

__author__ = "Noah Hummel"

from kubernetes import client
from kubernetes.client.rest import ApiException
import logger

log = logger.get(__name__)

def scale_deployment(namespace: str, name: str, replicas: int):
    try:
        log.debug(f"Scaling deployment {name} in {namespace} to {replicas}")
        appsV1 = client.AppsV1Api()
        original_spec = appsV1.read_namespaced_deployment(name, namespace)
        updated_spec = client.AppsV1beta1DeploymentSpec(replicas=replicas, template=original_spec)
        updated_deployment = client.AppsV1beta1Deployment(spec=updated_spec)
        appsV1.patch_namespaced_deployment_scale(name, namespace, updated_deployment)
    except ApiException as e:
        sentry_sdk.capture_exception(e)
