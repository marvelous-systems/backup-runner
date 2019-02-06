import os

__author__ = "Noah Hummel"

from kubernetes import client, config
import logger
import argparse

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
    log = logger.get()
    args = parser.parse_args()

    log.debug("Backup runner started.")

    if os.environ.get("KUBERNETES_PORT"):
        log.debug("Running inside cluster")
        config.load_incluster_config()
    else:
        log.debug("Running outside of cluster")
        config.load_kube_config("/kube/config")

