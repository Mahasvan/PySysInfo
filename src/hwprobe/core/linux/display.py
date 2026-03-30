import os
import re
from typing import Optional

from hwprobe.core.common.edid import parse_edid
from hwprobe.core.linux.common import pci_path_linux
from hwprobe.models.display_models import DisplayInfo, DisplayModuleInfo

_PCI_BDF_PATTERN = re.compile(r"^[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]$")


def _extract_pci_bdf_from_sysfs_path(path: str) -> Optional[str]:
    """Extract the endpoint PCI BDF from a resolved sysfs path."""
    parts = [part for part in path.strip().split(os.path.sep) if part]
    bdf_candidates = [part for part in parts if _PCI_BDF_PATTERN.match(part)]
    return bdf_candidates[-1] if bdf_candidates else None


def _fetch_individual_monitor_info(device_path: str) -> Optional[DisplayModuleInfo]:
    edid_path = os.path.join(device_path, "edid")
    if not os.path.exists(edid_path): return None
    parent_path = os.path.join(device_path, "device")

    # todo: populate parent graphics card info
    # we have vendor and device ids of the parent gpu. When PCI-IDs integration is done, use it to get name

    with open(edid_path, "rb") as f:
        edid_data = f.read()
    if len(edid_data) == 0: return None

    monitor_data = parse_edid(edid_data)

    pci_path_full = os.path.realpath(parent_path)
    pci_bdf = _extract_pci_bdf_from_sysfs_path(pci_path_full)
    if pci_bdf:
        monitor_data.pci_path = pci_path_linux(pci_bdf)

    acpi_file = os.path.join(device_path, "firmware_node", "path")
    if os.path.exists(acpi_file):
        with open(acpi_file, "r") as f:
            monitor_data.acpi_path = f.read().strip()

    return monitor_data


def fetch_display_info():
    display_info = DisplayInfo()
    pattern = re.compile(r"^card\d+$")
    root_path = "/sys/class/drm"
    parent_devices = os.listdir(root_path)
    parent_devices = [os.path.join(root_path, device) for device in parent_devices if pattern.match(device)]

    for parent_path in parent_devices:
        children = [x for x in os.listdir(parent_path) if x.startswith("card")]
        for child in children:
            response = _fetch_individual_monitor_info(os.path.join(parent_path, child))
            if response:
                display_info.modules.append(response)

    return display_info
