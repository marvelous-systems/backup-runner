import sentry_sdk
import yaml
from datetime import timedelta

import os
import argparse

from kubernetes import config, client
from kubernetes.client import V1Deployment
from kubernetes.client.rest import ApiException

import logger
from k8s import wait_for_reconciliation_blocking
from mutations.deployment import create_deployment
from mutations.scale import update_deployment_scale
from sidecar_deploy import new_backup_sidecar_deployment_with_volumes
from views.persistentVolumeClaim import list_pvcs_for_deployment
from views.pod import list_pods_for_deployment

__author__ = "Noah Hummel"


parser = argparse.ArgumentParser(
    description="Perform an offline backup of a kubernetes deployment."
)
parser.add_argument(
    "namespace",
    type=str,
    help="Kubernetes namespace of the deployment"
)
parser.add_argument(
    "deployment",
    type=str,
    help="Name of the deployment"
)
parser.add_argument(
    "store",
    type=str,
    help="Name of the secret with information about the backup location"
)
operations = parser.add_mutually_exclusive_group()
operations.add_argument("-b", "--backup", action="store_true",
                        help="Perform a backup of all attached volumes")
operations.add_argument("-r", "--snapshot", type=str, nargs="+",
                        help="Perform a restore of the given snapshots")

if __name__ == "__main__":
    args = parser.parse_args()
    log = logger.get(__name__)

    log.debug("Backup runner started.")

    if os.environ.get("KUBERNETES_PORT"):
        log.debug("Running inside cluster")
        config.load_incluster_config()

        with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as f:
            token = f.read()
            log.debug(f"Using ServiceAccount token {token[:8]}...{token[-8:]}")
    else:
        log.debug("Running outside of cluster")
        config.load_kube_config("/kube/config")

    api = client.AppsV1Api()
    try:
        deployment: V1Deployment = api.read_namespaced_deployment(
            args.deployment, args.namespace)
    except ApiException as e:
        sentry_sdk.capture_exception(e)
        log.debug(f"Deployment {args.namespace}/{args.deployment} does not "
                  f"exist or can't be fetched.")
        exit(1)

    pvcs = list_pvcs_for_deployment(args.deployment, args.namespace)
    for pvc in pvcs:
        log.debug(f"Deployment has PVC {pvc.metadata.name} "
                  f"provided by {pvc.spec.storage_class_name} "
                  f"in phase {pvc.status.phase}")

    pods = list_pods_for_deployment(args.deployment, args.namespace)
    for pod in pods:
        log.debug(f"Deployment has Pod {pod.metadata.name}")

    update_deployment_scale(args.deployment, args.namespace, 0)
    wait_for_reconciliation_blocking(
        lambda xs: len(xs) == 0,
        timedelta(minutes=1),
        list_pods_for_deployment,
        args.deployment,
        args.namespace
    )
    pods = list_pods_for_deployment(args.deployment, args.namespace)
    log.debug(f"Deployment has {len(pods)} Pods remaining.")

    if args.backup:
        sidecar_deployment = new_backup_sidecar_deployment_with_volumes(
            deployment.to_dict(), args.store)
        sidecar = create_deployment(sidecar_deployment, args.namespace)
        log.debug(sidecar)

    elif args.snapshot:
        log.warning("Restore operation is not yet implemented.")
        pass

    update_deployment_scale(args.deployment, args.namespace, deployment.spec.replicas)
    wait_for_reconciliation_blocking(
        lambda xs: len(xs) == 0,
        timedelta(minutes=1),
        list_pods_for_deployment,
        args.deployment,
        args.namespace
    )
