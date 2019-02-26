from datetime import timedelta

import os
import argparse

from kubernetes import config, client

import logger
from k8s import wait_for_reconciliation
from mutations.scale import scale_deployment
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
operations.add_argument("-b", "--backup", type=str, nargs="+",
                        help="Perform a backup of the given paths")
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
        appsV1Api = client.AppsV1Api()
        available_resources = appsV1Api.get_api_resources()
        log.debug(f"Available resources: \n{available_resources}")
    else:
        log.debug("Running outside of cluster")
        config.load_kube_config("/kube/config")

    pvcs = list_pvcs_for_deployment(args.deployment, args.namespace)
    for pvc in pvcs:
        log.debug(f"Deployment has PVC {pvc.metadata.name} "
                  f"provided by {pvc.spec.storage_class_name} "
                  f"in phase {pvc.status.phase}")

    pods = list_pods_for_deployment(args.deployment, args.namespace)
    for pod in pods:
        log.debug(f"Deployment has Pod {pod.metadata.name}")

    scale_deployment(args.deployment, args.namespace, 0)
    wait_for_reconciliation(
        lambda xs: len(xs) == 0,
        timedelta(minutes=1),
        list_pods_for_deployment,
        args.deployment,
        args.namespace
    )
    pods = list_pods_for_deployment(args.deployment, args.namespace)
    log.debug(f"Deployment has {len(pods)} Pods remaining.")