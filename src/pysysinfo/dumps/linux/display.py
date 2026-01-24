import os
import re
from typing import Optional

from pysysinfo.dumps.common.edid import parse_edid
from pysysinfo.models.display_models import DisplayInfo, DisplayModuleInfo


def _fetch_individual_monitor_info(device_path: str, parent_device_path: str) -> Optional[DisplayModuleInfo]:
    path = os.path.join(device_path, "edid")
    if not os.path.exists(path): return None
    # todo: populate parent graphics card info
    with open(path, "rb") as f:
        edid_data = f.read()
    if len(edid_data) == 0: return None
    return parse_edid(edid_data)


def fetch_display_info():
    display_info = DisplayInfo()
    pattern = re.compile(r"^card\d+$")
    root_path = "/sys/class/drm"
    parent_devices = os.listdir(root_path)
    parent_devices = [os.path.join(root_path, device) for device in parent_devices if pattern.match(device)]

    for parent_path in parent_devices:
        children = [x for x in os.listdir(parent_path) if x.startswith("card")]
        for child in children:
            response = _fetch_individual_monitor_info(os.path.join(parent_path, child), parent_path)
            if response:
                display_info.modules.append(response)

    return display_info
