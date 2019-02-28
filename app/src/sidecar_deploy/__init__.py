import os

import yaml
from typing import List, Dict

import logger
from algorithm import new_volume_mounts_with_canonical_mount_path
from k8s.resource import to_camel_case
from k8s.resource.deployment import get_volumes, copy_volumes

__author__ = "Noah Hummel"
log = logger.get(__name__)


def _from_secret(variable_name: str, secret_name: str, secret_key: str) -> dict:
    return {
        "name": variable_name,
        "valueFrom": {
            "secretKeyRef": {
                "name": secret_name,
                "key": secret_key
            }
        }
    }


def new_backup_sidecar_deployment(backup_paths: List[str],
                                  store_secret_name: str) -> Dict:
    """Generates a k8s Deployment for the restic-backup-sidecar container.

    Args:
        backup_paths:
            List of paths to back up.
        store_secret_name:
            Name of k8s secret with configuration of backup location.

    Returns:
        A k8s Deployment for the restic-backup-sidecar container as Dict
    """
    with open("/app/src/sidecar_deploy/backup.yml") as f:
        deployment: Dict = yaml.safe_load(f)

    # backup sidecar configuration
    deployment_name = deployment["metadata"]["name"] + f"-{os.urandom(16).hex()}"
    deployment["metadata"]["name"] = deployment_name
    deployment["metadata"]["labels"]["app"] = deployment_name
    deployment["spec"]["selector"]["matchLabels"]["app"] = deployment_name
    deployment["spec"]["template"]["metadata"]["labels"]["app"] = \
        deployment_name
    deployment["spec"]["template"]["spec"]["volumes"][0]["secret"]\
        ["secretName"] = store_secret_name
    deployment["spec"]["template"]["spec"]["containers"][0]["name"] = \
        deployment_name
    deployment["spec"]["template"]["spec"]["containers"][0]["env"] = [
        _from_secret("SFTP_PATH", store_secret_name, "path"),
        _from_secret("SFTP_USER", store_secret_name, "user"),
        _from_secret("SFTP_HOST", store_secret_name, "host"),
        _from_secret("RESTIC_PASSWORD", store_secret_name, "restic_password"),
        {
            "name": "BACKUP_PATHS",
            "value": ",".join(backup_paths)
        }
    ]

    return deployment


def new_backup_sidecar_deployment_with_volumes(deployment: Dict,
                                               store_secret_name: str) -> Dict:
    volumes = get_volumes(deployment, exclude_secrets=True)
    volume_mounts = new_volume_mounts_with_canonical_mount_path(volumes)
    backup_paths = [vm["mountPath"] for vm in volume_mounts]
    sidecar_deployment = new_backup_sidecar_deployment(backup_paths,
                                                       store_secret_name)
    sidecar_deployment = copy_volumes(deployment, sidecar_deployment)
    sidecar_deployment["spec"]["template"]["spec"]["containers"][0]\
        ["volumeMounts"].extend(volume_mounts)

    mounting_table = [f"{vm['name']} -> {vm['mountPath']}" for vm in
                      volume_mounts]
    log.debug(f"Created mounting table: {mounting_table}")
    return to_camel_case(sidecar_deployment)
