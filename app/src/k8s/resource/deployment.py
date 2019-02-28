from typing import List, Dict

import logger
from k8s.resource import strip_null

__author__ = "Noah Hummel"
log = logger.get(__name__)


def copy_volumes(from_deployment: Dict, to_deployment: Dict) -> Dict:
    """Copies volumes from Deployment to Deployment.

    Does not copy volumes for mounted secrets.

    Args:
        from_deployment:
            Deployment whose volumes are copied.
        to_deployment:
            Deployment who will receive from_deployments' volumes.

    Returns:
        The resulting Deployment.
    """

    # attaching the volumes of the original deployment to this one
    volumes: List[Dict] = get_volumes(from_deployment, exclude_secrets=True)
    to_deployment["spec"]["template"]["spec"]["volumes"].extend(volumes)
    return to_deployment


def get_volumes(deployment: Dict, exclude_secrets: bool=False) -> List[Dict]:
    """Returns all volumes defined in a k8s Deployment.

    Volumes can either be defined in Deployment.spec or
    Deployment.spec.template.spec.

    Args:
        deployment:
            Deployment whose volumes to get, as dict.
        exclude_secrets:
            If True, volumes for mounted secrets will be excluded.

    Returns:
        List of volumes for Deployment as dict.
    """

    volumes = [strip_null(v) for v in
               deployment["spec"]["template"]["spec"]["volumes"]]

    if exclude_secrets:
        return [v for v in volumes if "secret" not in v]
    return volumes