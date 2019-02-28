
import sentry_sdk
from typing import List
from kubernetes import client
from kubernetes.client import V1PersistentVolumeClaim
from kubernetes.client.rest import ApiException
from views.volume import list_volumes_for_deployment
import logger


log = logger.get(__name__)
__author__ = "Noah Hummel"


def list_pvcs_for_deployment(name: str, namespace: str) \
        -> List[V1PersistentVolumeClaim]:
    try:
        volumes = list_volumes_for_deployment(name, namespace)
        if not volumes:
            log.debug("Deployment has no volumes")
            return []

        api = client.CoreV1Api()
        pvcs = []
        for volume in volumes:
            log.debug(f"Deployment {name} has volume {volume.name}")

            if volume.persistent_volume_claim is None:
                log.debug(f"Volume {volume.name} was not dynamically provided, "
                          f"skipping.")
                continue

            claim = volume.persistent_volume_claim
            log.debug(f"Volume {volume.name} was dynamically provided for PVC "
                      f"{claim.claim_name}")
            pvcs.append(api.read_namespaced_persistent_volume_claim(
                claim.claim_name, namespace))

        return pvcs

    except ApiException as e:
        sentry_sdk.capture_exception(e)
