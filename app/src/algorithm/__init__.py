import sentry_sdk
import os
from typing import Dict, Union, List

from k8s.resource import to_camel_case

__author__ = "Noah Hummel"


class VolumeNameFormatError(Exception):
    pass


def get_canonical_mount_path(volume: Dict, name_map: Dict[str, str]=None) \
        -> Union[os.PathLike, str]:
    """Returns the canonical mountPath for a given volume.

    Args:
        volume: A kubernetes volume as Dict.
        name_map:
            Dict mapping volume names, this allows volumes to be mapped to
            canonical mountPaths of other volumes. Example:

            The volume "some-volume" would mount to "/some-volume"
            Using the following name_map, "some-volume" would be mounted
            to "/some-other-volume" the canonical mountPath of
            "some-other-volume":

             >>> name_map = {"some-volume": "some-other-volume"}

    Raises:
        VolumeNameFormatError:
            If the resulting canonical mountPath is not a valid path.

    Returns:
        The canonical mountPath for the given volume.
    """
    if "name" not in volume:  # volume is V1Volume as Dict
        volume_name = volume["metadata"]["name"]
    else:  # volume is part of pod spec
        volume_name = volume["name"]

    if name_map:
        if volume_name in name_map:
            volume_name = name_map[volume_name]

    volume_name = volume_name.replace("/", "--")
    if volume_name.startswith("."):
        volume_name = f"DOT--{volume_name[1:]}"
    try:
        mount_path = os.path.join("/", volume_name)
        if not os.path.isabs(mount_path):
            raise ValueError
    except (TypeError, AttributeError, BytesWarning, ValueError) as e:
        sentry_sdk.capture_exception(e)
        raise VolumeNameFormatError

    return mount_path


def new_volume_mounts_with_canonical_mount_path(
        for_volumes: List[Dict],
        name_map: Dict[str, str]=None,
        sub_path_map: Dict[str, str]=None) -> List[Dict]:
    """Creates a list of canonical volumeMounts for a given list of Volumes.

    Args:
        for_volumes: List of volumes to create volumeMounts for.
        name_map:
            Dict mapping volume names, this allows volumes to be mapped to
            canonical mountPaths of other volumes. See get_canonical_mount_path.
        sub_path_map:
            Dict mapping volume names to subPaths. This allows the resulting
            mountPath to only include a certain subPath for a certain volume.
            Example:

                >>> sub_path_map = {"some-volume": "some/sub/path"}

    Returns:
        List of volumeMounts for the given volumes.
    """
    volume_mounts = [{
        "name": v["name"],
        "mountPath": get_canonical_mount_path(v, name_map)
    } for v in for_volumes]

    if sub_path_map:
        return [{**vm, "subPath": sub_path_map[vm["name"]]}
                if vm["name"] in sub_path_map else vm
                for vm in volume_mounts]
    return [to_camel_case(vm) for vm in volume_mounts]
