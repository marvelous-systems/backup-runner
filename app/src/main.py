import sys

import os

__author__ = "Noah Hummel"

import logging

from kubernetes import client, config


if __name__ == "__main__":
    logger = logging.getLogger("backup-runner")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if os.environ.get("KUBERNETES_PORT"):  # running inside cluster
        config.load_incluster_config()
    else:
        config.load_kube_config("/kube/config")

    appsV1 = client.AppsV1Api()
    logger.debug("Hello, Kubernetes!")
    logger.debug(appsV1.list_deployment_for_all_namespaces())
