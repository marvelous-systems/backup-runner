import os

__author__ = "Noah Hummel"

from kubernetes import client, config
import logger

if __name__ == "__main__":
    log = logger.get()

    if os.environ.get("KUBERNETES_PORT"):  # running inside cluster
        config.load_incluster_config()
    else:
        config.load_kube_config("/kube/config")

    log.debug("Backup runner started.")
